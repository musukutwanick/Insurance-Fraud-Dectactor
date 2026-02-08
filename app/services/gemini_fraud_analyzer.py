"""
Advanced fraud analysis service using Google Gemini AI.

Provides:
- AI-powered fraud detection reasoning
- Pattern analysis across claims
- Risk assessment with explanations
- Anomaly detection
"""

from typing import Dict, Any, List, Optional
from google import genai
from app.core.config import settings
from app.core.logging_config import get_logger
import json
import io
from PIL import Image
import httpx

logger = get_logger(__name__)


class GeminiFraudAnalyzer:
    """Service for AI-powered fraud analysis using Google Gemini."""
    
    def __init__(self):
        """Initialize Gemini model for fraud analysis."""
        if settings.gemini_api_key:
            self.client = genai.Client(api_key=settings.gemini_api_key)
            self.model_name = settings.gemini_model
            self.config = {
                "temperature": settings.gemini_temperature,
                "max_output_tokens": settings.gemini_max_tokens,
            }
            logger.info(f"Gemini fraud analyzer initialized with model: {settings.gemini_model}")
        else:
            self.client = None
            logger.warning("Gemini API key not configured - fraud analysis will use basic heuristics")
    
    async def analyze_claim_fraud_risk(
        self,
        incident_type: str,
        damage_description: str,
        location_zone: str,
        image_analysis: Optional[str],
        image_bytes_list: Optional[List[bytes]],
        image_urls: Optional[List[str]],
        similar_incidents: List[Dict[str, Any]],
        temporal_pattern_score: float,
        spatial_cluster_score: float,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive fraud risk analysis using Gemini AI.
        
        Args:
            incident_type: Type of incident
            damage_description: Claimant's description
            location_zone: Anonymized location
            image_analysis: Analysis of damage images
            similar_incidents: List of similar historical incidents
            temporal_pattern_score: Score from temporal pattern analysis
            spatial_cluster_score: Score from spatial clustering
            
        Returns:
            Dictionary with fraud risk assessment and reasoning
        """
        if not self.client:
            return self._fallback_analysis(
                incident_type,
                damage_description,
                temporal_pattern_score,
                spatial_cluster_score,
                len(similar_incidents)
            )
        
        try:
            if image_analysis is None and image_urls:
                image_analysis = await self._analyze_images_with_urls(image_urls)

            if image_analysis is None and image_bytes_list:
                image_analysis = self._analyze_images_with_gemini(image_bytes_list)

            # Build analysis prompt
            prompt = self._build_fraud_analysis_prompt(
                incident_type=incident_type,
                damage_description=damage_description,
                location_zone=location_zone,
                image_analysis=image_analysis,
                similar_incidents=similar_incidents,
                temporal_pattern_score=temporal_pattern_score,
                spatial_cluster_score=spatial_cluster_score,
            )
            
            # Get Gemini analysis
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.config
            )
            analysis_text = response.text
            
            # Parse structured output
            result = self._parse_gemini_response(analysis_text)
            
            logger.info(f"Gemini fraud analysis completed: risk={result['fraud_risk_level']}")
            return result
            
        except Exception as e:
            logger.error(f"Error in Gemini fraud analysis: {e}")
            return self._fallback_analysis(
                incident_type,
                damage_description,
                temporal_pattern_score,
                spatial_cluster_score,
                len(similar_incidents)
            )
    
    def _build_fraud_analysis_prompt(
        self,
        incident_type: str,
        damage_description: str,
        location_zone: str,
        image_analysis: Optional[str],
        similar_incidents: List[Dict[str, Any]],
        temporal_pattern_score: float,
        spatial_cluster_score: float,
    ) -> str:
        """Build comprehensive fraud analysis prompt for Gemini."""
        
        similar_summary = "\n".join([
            f"- Similar incident {i+1}: {inc.get('incident_type', 'unknown')}, "
            f"Company: {inc.get('organization_name', 'Unknown')}, "
            f"Location: {inc.get('location_zone', 'N/A')}, "
            f"Overall Similarity: {inc.get('overall_similarity', 0):.2%}, "
            f"Image: {inc.get('image_similarity', 0):.2%}, "
            f"Date: {inc.get('incident_date', 'N/A')}"
            for i, inc in enumerate(similar_incidents[:5])
        ]) if similar_incidents else "No similar incidents found"
        
        image_info = image_analysis if image_analysis else "No image analysis available"
        
        prompt = f"""You are an expert insurance fraud investigator. Analyze this insurance claim for fraud risk.

**CRITICAL: This system searches for similar claims across ALL insurance companies to detect cross-company fraud patterns.**

**Claim Details:**
- Incident Type: {incident_type}
- Location Zone: {location_zone}
- Damage Description: {damage_description}

**Image Analysis:**
{image_info}

**Pattern Analysis:**
- Temporal Pattern Score: {temporal_pattern_score:.2f} (higher = more unusual timing)
- Spatial Cluster Score: {spatial_cluster_score:.2f} (higher = more clustering in location)
- Similar Historical Incidents Found: {len(similar_incidents)}

**Similar Incidents (ACROSS ALL COMPANIES):**
{similar_summary}

**IMPORTANT: If similar incidents are found from different companies, this is a major red flag for fraud!**

**Analysis Tasks:**
1. Assess the overall fraud risk (LOW, MEDIUM, HIGH, CRITICAL)
2. Identify specific red flags or suspicious patterns
3. Check if the same incident was filed with multiple companies (major fraud indicator)
4. Evaluate consistency between description, images, and patterns
5. Consider the context of similar incidents and their companies
6. Provide reasoning for your assessment

**Output Format (JSON):**
{{
    "fraud_risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
    "fraud_score": 0.0-1.0,
    "confidence": 0.0-1.0,
    "red_flags": ["flag1", "flag2", ...],
    "reasoning": "Detailed explanation including company information if cross-company matches found",
    "recommendations": ["recommendation1", "recommendation2", ...],
    "cross_company_fraud_detected": true/false
}}

Provide ONLY the JSON output, no additional text."""
        
        return prompt

    def _analyze_images_with_gemini(self, image_bytes_list: List[bytes]) -> Optional[str]:
        if not self.client:
            return None

        try:
            analyses = []
            prompt = (
                "You are a claims adjuster. Analyze the image and summarize: "
                "damage type, severity, location of damage, and any anomalies. "
                "Keep it under 3 sentences."
            )

            for idx, image_bytes in enumerate(image_bytes_list[:5]):
                image = Image.open(io.BytesIO(image_bytes))
                response = self.client.models.generate_content(
                    model=settings.gemini_vision_model,
                    contents=[prompt, image]
                )
                summary = (response.text or "").strip()
                if summary:
                    analyses.append(f"Image {idx + 1}: {summary}")

            return "\n".join(analyses) if analyses else None
        except Exception as e:
            logger.error(f"Error analyzing images with Gemini Vision: {e}")
            return None

    async def _analyze_images_with_urls(self, image_urls: List[str]) -> Optional[str]:
        if not self.client:
            return None

        try:
            analyses = []
            prompt = (
                "You are a claims adjuster. Analyze the image and summarize: "
                "damage type, severity, location of damage, and any anomalies. "
                "Keep it under 3 sentences."
            )

            async with httpx.AsyncClient(timeout=20) as http_client:
                for idx, image_url in enumerate(image_urls[:5]):
                    response = await http_client.get(image_url)
                    response.raise_for_status()
                    image = Image.open(io.BytesIO(response.content))
                    vision_response = self.client.models.generate_content(
                        model=settings.gemini_vision_model,
                        contents=[prompt, image]
                    )
                    summary = (vision_response.text or "").strip()
                    if summary:
                        analyses.append(f"Image {idx + 1}: {summary}")

            return "\n".join(analyses) if analyses else None
        except Exception as e:
            logger.error(f"Error analyzing images via signed URLs: {e}")
            return None
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini's JSON response."""
        try:
            # Extract JSON from response (may have markdown formatting)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()
            
            result = json.loads(json_text)
            
            # Validate required fields
            required_fields = ["fraud_risk_level", "fraud_score", "reasoning"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure proper types
            result["fraud_score"] = float(result["fraud_score"])
            result["confidence"] = float(result.get("confidence", 0.8))
            result["red_flags"] = result.get("red_flags", [])
            result["recommendations"] = result.get("recommendations", [])
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            logger.debug(f"Response text: {response_text}")
            raise
    
    def _fallback_analysis(
        self,
        incident_type: str,
        damage_description: str,
        temporal_pattern_score: float,
        spatial_cluster_score: float,
        similar_count: int,
    ) -> Dict[str, Any]:
        """Fallback fraud analysis using heuristics when Gemini is unavailable."""
        
        # If no similar incidents, default to LOW risk
        if similar_count == 0:
            return {
                "fraud_risk_level": "LOW",
                "fraud_score": 0.1,
                "confidence": 0.7,
                "red_flags": ["No similar historical incidents found"],
                "reasoning": "First-time pattern. No historical matches found for comparison. Standard verification recommended.",
                "recommendations": [
                    "Process as new claim pattern",
                    "Standard documentation verification",
                    "Monitor for future similar patterns"
                ]
            }
        
        # Simple heuristic scoring
        risk_score = 0.0
        red_flags = []
        
        # Check temporal patterns
        if temporal_pattern_score > 0.7:
            risk_score += 0.3
            red_flags.append("Unusual timing pattern detected")
        
        # Check spatial clustering
        if spatial_cluster_score > 0.7:
            risk_score += 0.3
            red_flags.append("High concentration of incidents in area")
        
        # Check similar incidents
        if similar_count > 5:
            risk_score += 0.2
            red_flags.append(f"Multiple similar incidents found ({similar_count})")
        
        # Check description length (too short or too long can be suspicious)
        desc_len = len(damage_description)
        if desc_len < 50:
            risk_score += 0.1
            red_flags.append("Insufficient damage description")
        elif desc_len > 2000:
            risk_score += 0.05
            red_flags.append("Unusually detailed description")
        
        # Determine risk level
        if risk_score >= 0.75:
            risk_level = "CRITICAL"
        elif risk_score >= 0.5:
            risk_level = "HIGH"
        elif risk_score >= 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "fraud_risk_level": risk_level,
            "fraud_score": min(risk_score, 1.0),
            "confidence": 0.6,  # Lower confidence for heuristic analysis
            "red_flags": red_flags if red_flags else ["No significant red flags detected"],
            "reasoning": "Basic heuristic analysis (Gemini AI unavailable). Review flagged patterns manually.",
            "recommendations": [
                "Manual review recommended for claims with multiple red flags",
                "Consider requesting additional documentation",
                "Verify claimant identity and history"
            ]
        }


# Singleton instance
gemini_fraud_analyzer = GeminiFraudAnalyzer()
