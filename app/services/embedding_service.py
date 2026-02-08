"""
Service layer for AI embeddings and similarity analysis.

Handles:
- Text and image embedding generation using Google Gemini
- Fingerprint generation (spatio-temporal)
- Historical incident matching
- Fraud risk scoring

Integrated with Google Gemini API for production-ready AI capabilities.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import IncidentFingerprint
from app.core.logging_config import get_logger
from app.core.config import settings
from google import genai

logger = get_logger(__name__)

# Configure Gemini API
if settings.gemini_api_key:
    gemini_client = genai.Client(api_key=settings.gemini_api_key)
    logger.info("Gemini API configured successfully")
else:
    gemini_client = None
    logger.warning("Gemini API key not found - using fallback embeddings")


class EmbeddingService:
    """Service for generating embeddings from text and images using Google Gemini."""

    @staticmethod
    async def generate_text_embedding(text: str) -> List[float]:
        """
        Generate a text embedding from damage description using Gemini API.
        
        Uses Google's text-embedding-004 model for high-quality embeddings.
        Falls back to hash-based embeddings if API is unavailable.
        
        Args:
            text: Damage description text
            
        Returns:
            List of floats representing text embedding (768-dim vector for Gemini)
        """
        try:
            if gemini_client:
                # Use Gemini Embeddings API with new SDK
                response = gemini_client.models.embed_content(
                    model=settings.gemini_embedding_model,
                    contents=text
                )
                embedding = response.embeddings[0].values
                logger.debug(f"Generated Gemini text embedding: {len(embedding)} dimensions")
                return embedding
            else:
                # Fallback to hash-based embedding
                return EmbeddingService._generate_fallback_embedding(text.encode())
                
        except Exception as e:
            logger.error(f"Error generating Gemini embedding: {e}, using fallback")
            return EmbeddingService._generate_fallback_embedding(text.encode())

    @staticmethod
    async def generate_image_embedding(image_bytes: bytes) -> List[float]:
        """
        Generate an image embedding from damage image using Gemini Vision.
        
        Uses Gemini's multimodal capabilities to understand damage images.
        Falls back to hash-based embeddings if API is unavailable.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            List of floats representing image embedding
        """
        try:
            if gemini_client:
                # Use Gemini Vision for image understanding
                # Generate a description first, then embed it
                
                # Create image part
                import PIL.Image
                import io
                image = PIL.Image.open(io.BytesIO(image_bytes))
                
                # Get image description
                prompt = """Analyze this insurance damage image and describe:
1. Type of damage visible
2. Severity of damage
3. Location of damage
4. Any identifying features
Be concise and factual."""
                
                response = gemini_client.models.generate_content(
                    model=settings.gemini_vision_model,
                    contents=[prompt, image]
                )
                description = response.text
                
                # Embed the description
                embed_response = gemini_client.models.embed_content(
                    model=settings.gemini_embedding_model,
                    contents=description
                )
                embedding = embed_response.embeddings[0].values
                logger.debug(f"Generated Gemini image embedding: {len(embedding)} dimensions")
                return embedding
            else:
                # Fallback to hash-based embedding
                return EmbeddingService._generate_fallback_embedding(image_bytes)
                
        except Exception as e:
            logger.error(f"Error generating Gemini image embedding: {e}, using fallback")
            return EmbeddingService._generate_fallback_embedding(image_bytes)
    
    @staticmethod
    def _generate_fallback_embedding(data: bytes, dim: int = 768) -> List[float]:
        """
        Generate a deterministic hash-based embedding as fallback.
        
        Args:
            data: Data to hash
            dim: Embedding dimension
            
        Returns:
            List of floats representing hash-based embedding
        """
        data_hash = hashlib.sha256(data).digest()
        embedding = []
        for i in range(dim):
            byte_val = data_hash[i % len(data_hash)]
            embedding.append(float(byte_val) / 255.0)
        return embedding


class FingerprintService:
    """Service for generating and managing incident fingerprints."""

    @staticmethod
    def generate_spatial_fingerprint(location_zone: str) -> str:
        """
        Generate a spatial fingerprint from location zone.
        
        Creates a hash that represents the geographic area but is anonymized.
        
        Args:
            location_zone: Generalized location zone (e.g., "zone_a")
            
        Returns:
            Spatial fingerprint hash (hex string)
        """
        # Create spatial hash from zone
        spatial_hash = hashlib.md5(location_zone.encode()).hexdigest()[:16]
        return spatial_hash

    @staticmethod
    def generate_temporal_fingerprint(
        incident_date: datetime,
        time_window_start: datetime,
        time_window_end: datetime
    ) -> str:
        """
        Generate a temporal fingerprint from incident time window.
        
        Creates a hash based on:
        - Day of week
        - Month
        - Hour (generalized to 4-hour windows)
        - Day of month
        
        Args:
            incident_date: Approximate incident date
            time_window_start: Start of time window
            time_window_end: End of time window
            
        Returns:
            Temporal fingerprint hash (hex string)
        """
        # Extract temporal features
        day_of_week = incident_date.strftime("%A")
        month = incident_date.strftime("%B")
        hour_window = (incident_date.hour // 4) * 4  # 4-hour windows
        day_of_month = incident_date.day
        
        # Create temporal string
        temporal_str = f"{day_of_week}_{month}_{hour_window}h_{day_of_month}d"
        
        # Hash it
        temporal_hash = hashlib.md5(temporal_str.encode()).hexdigest()[:16]
        return temporal_hash

    @staticmethod
    def calculate_damage_severity_score(
        damage_description: str,
        image_count: int
    ) -> float:
        """
        Estimate damage severity from description and image count.
        
        PLACEHOLDER: Returns a simple heuristic score.
        
        In production: Use ML model trained on claims data.
        
        Args:
            damage_description: Text description of damage
            image_count: Number of damage images
            
        Returns:
            Severity score (0.0 to 1.0)
        """
        # Simple heuristic
        severity = 0.0
        
        # Length of description indicates detail/severity
        severity += min(len(damage_description) / 1000, 0.3)
        
        # Number of images indicates documentation level
        severity += min(image_count / 10, 0.3)
        
        # Keyword-based indicators
        high_severity_words = {
            "total loss", "critical", "severe", "major", "extensive",
            "destroyed", "crushed", "fire", "explosion", "collision"
        }
        
        text_lower = damage_description.lower()
        keyword_matches = sum(1 for word in high_severity_words if word in text_lower)
        severity += min(keyword_matches / 5, 0.4)
        
        return min(severity, 1.0)


class SimilarityService:
    """Service for computing similarity between incidents."""

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            vec1: First embedding vector
            vec2: Second embedding vector
            
        Returns:
            Similarity score (0.0 to 1.0, where 1.0 is identical)
        """
        arr1 = np.array(vec1)
        arr2 = np.array(vec2)
        
        # Cosine similarity
        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        # Normalize to 0-1 range (cosine similarity is -1 to 1)
        return max(0.0, (similarity + 1) / 2)

    @staticmethod
    def hamming_distance(hash1: str, hash2: str) -> float:
        """
        Compute normalized Hamming distance between two hex strings.
        
        Used for comparing spatial/temporal fingerprints.
        
        Args:
            hash1: First fingerprint hash
            hash2: Second fingerprint hash
            
        Returns:
            Similarity score (0.0 to 1.0, where 1.0 is identical)
        """
        if len(hash1) != len(hash2):
            return 0.0
        
        # Count differing characters
        differences = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
        
        # Normalize: 1.0 if identical, 0.0 if completely different
        similarity = 1.0 - (differences / len(hash1))
        return similarity

    @staticmethod
    async def find_similar_incidents(
        db: AsyncSession,
        new_text_embedding: List[float],
        new_image_embedding: List[float],
        spatial_fingerprint: str,
        temporal_fingerprint: str,
        incident_type: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find similar historical incidents across ALL insurance companies.
        
        Compares against stored fingerprints using:
        - Embedding similarity (cosine distance)
        - Fingerprint matching (Hamming distance)
        - Incident type matching
        
        Args:
            db: Database session
            new_text_embedding: Text embedding of new claim
            new_image_embedding: Image embedding of new claim
            spatial_fingerprint: Spatial fingerprint of new claim
            temporal_fingerprint: Temporal fingerprint of new claim
            incident_type: Incident type code
            limit: Maximum number of results
            
        Returns:
            List of similar incidents with similarity scores and company info
        """
        # Fetch ALL historical fingerprints to compare against
        # Use eager loading to fetch related claim and user data
        from app.models import Claim, User
        
        stmt = (
            select(IncidentFingerprint)
            .join(IncidentFingerprint.claim)
            .join(Claim.submitted_by)
            .options(
                selectinload(IncidentFingerprint.claim).selectinload(Claim.submitted_by)
            )
        )  # Fetch ALL historical fingerprints with relationships
        result = await db.execute(stmt)
        historical = result.scalars().all()
        
        logger.info(f"Comparing against {len(historical)} historical incidents in database")
        
        matches = []
        
        for incident in historical:
            try:
                # Access claim and user data (eagerly loaded)
                claim = incident.claim
                if not claim:
                    logger.warning(f"Fingerprint {incident.id} has no associated claim")
                    continue
                    
                user = claim.submitted_by
                if not user:
                    logger.warning(f"Claim {claim.claim_reference_id} has no associated user")
                    organization_name = "Unknown"
                else:
                    organization_name = user.organization_name or "Unknown"
                
                # Load embeddings from JSON
                stored_text_emb = incident.text_embedding
                stored_image_emb = incident.image_embedding
                
                # Compute similarities
                text_sim = SimilarityService.cosine_similarity(
                    new_text_embedding, stored_text_emb
                )
                image_sim = SimilarityService.cosine_similarity(
                    new_image_embedding, stored_image_emb
                )
                spatial_sim = SimilarityService.hamming_distance(
                    spatial_fingerprint, incident.spatial_fingerprint
                )
                temporal_sim = SimilarityService.hamming_distance(
                    temporal_fingerprint, incident.temporal_fingerprint
                )
                
                # Weighted overall similarity
                overall_similarity = (
                    text_sim * 0.25 +
                    image_sim * 0.35 +
                    spatial_sim * 0.20 +
                    temporal_sim * 0.20
                )
                
                # Log all comparisons for debugging
                logger.debug(
                    f"Comparing with fingerprint {incident.id}: "
                    f"overall={overall_similarity:.3f}, text={text_sim:.3f}, "
                    f"image={image_sim:.3f}, spatial={spatial_sim:.3f}, temporal={temporal_sim:.3f}"
                )
                
                if overall_similarity > 0.3:  # Lowered threshold to catch more similar claims
                    # Use already-accessed claim and organization data
                    matches.append({
                        "fingerprint_id": incident.id,
                        "overall_similarity": overall_similarity,
                        "text_similarity": text_sim,
                        "image_similarity": image_sim,
                        "spatial_similarity": spatial_sim,
                        "temporal_similarity": temporal_sim,
                        "incident_type": incident.incident_type_code,
                        "incident_date": claim.incident_date_approx,
                        "claim_reference_id": claim.claim_reference_id,
                        "organization_name": organization_name,
                        "location_zone": claim.location_zone,
                    })
                    logger.info(
                        f"Found similar incident: {claim.claim_reference_id} at {organization_name} "
                        f"(similarity: {overall_similarity:.1%})"
                    )
            except Exception as e:
                logger.warning(f"Error comparing with fingerprint {incident.id}: {e}")
                continue
        
        # Sort by similarity
        matches.sort(key=lambda x: x["overall_similarity"], reverse=True)
        return matches[:limit]


class FraudScoringService:
    """Service for computing fraud risk scores."""

    @staticmethod
    def calculate_fraud_risk_score(
        similarity_matches: List[Dict[str, Any]],
        damage_severity: float,
        matching_count: int
    ) -> Tuple[float, str, str]:
        """
        Calculate overall fraud risk score from multiple factors.
        
        Factors:
        - Number and quality of similar historical incidents
        - Damage severity
        - Pattern matching
        
        Args:
            similarity_matches: List of similar incidents with scores
            damage_severity: Damage severity score (0.0-1.0)
            matching_count: Number of matching incidents
            
        Returns:
            Tuple of (risk_score, risk_level, recommendation)
            where risk_score is 0.0-1.0
        """
        risk_score = 0.0
        
        if similarity_matches:
            # High similarity to historical incidents increases fraud risk
            top_similarity = similarity_matches[0]["overall_similarity"]
            risk_score += top_similarity * 0.6  # Weighted heavily
        
        # Multiple matches increase suspicion
        if matching_count > 2:
            risk_score += 0.2
        
        # Very low damage severity with high similarity is suspicious
        if damage_severity < 0.3 and similarity_matches:
            risk_score += 0.15
        
        # Cap at 1.0
        risk_score = min(risk_score, 1.0)
        
        # Determine risk level and recommendation
        if risk_score < 0.3:
            risk_level = "LOW"
            recommendation = "PROCEED"
        elif risk_score < 0.6:
            risk_level = "MEDIUM"
            recommendation = "HOLD"
        elif risk_score < 0.8:
            risk_level = "HIGH"
            recommendation = "INVESTIGATE"
        else:
            risk_level = "CRITICAL"
            recommendation = "INVESTIGATE"
        
        return risk_score, risk_level, recommendation
