"""
Service layer for claim processing and fraud analysis.

Handles:
- Claim submission processing
- Image handling and validation
- Fingerprint generation
- Fraud analysis orchestration
- Storage of anonymized incidents
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models import Claim, IncidentFingerprint, FraudAnalysisResult, User
from app.services.image_service import ImageProcessingService, ImageStorageService
from app.services.supabase_service import SupabaseMetadataService, map_severity_label
from app.services.embedding_service import (
    EmbeddingService,
    FingerprintService,
    SimilarityService,
    FraudScoringService,
)
from app.services.gemini_fraud_analyzer import gemini_fraud_analyzer
from app.core.logging_config import get_logger, get_audit_logger
import time

logger = get_logger(__name__)
audit_logger = get_audit_logger()


class ClaimProcessingService:
    """Service for processing insurance claims and analyzing fraud risk."""

    @staticmethod
    async def submit_and_analyze_claim(
        db: AsyncSession,
        user: User,
        incident_type: str,
        damage_description: str,
        location_zone: str,
        incident_date_approx: datetime,
        incident_time_window_start: datetime,
        incident_time_window_end: datetime,
        image_files: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Comprehensive claim submission and fraud analysis pipeline.
        
        Pipeline:
        1. Create claim record
        2. Process images (mask, validate, fingerprint)
        3. Generate embeddings
        4. Create incident fingerprint
        5. Compare against historical incidents
        6. Calculate fraud risk score
        7. Store results
        
        Args:
            db: Database session
            user: User submitting the claim
            incident_type: Type of incident
            damage_description: Description of damage
            location_zone: Generalized location zone
            incident_date_approx: Approximate incident date
            incident_time_window_start: Start of incident time window
            incident_time_window_end: End of incident time window
            image_files: Optional list of image bytes
            
        Returns:
            Dictionary with analysis results and claim reference ID
        """
        start_time = time.time()
        
        # Generate claim reference ID (anonymized)
        claim_reference_id = f"CLM-{str(uuid.uuid4())[:8]}"
        
        logger.info(f"Starting claim analysis: {claim_reference_id}")
        
        try:
            # Step 1: Create claim record
            claim = Claim(
                claim_reference_id=claim_reference_id,
                user_id=user.id,
                incident_type=incident_type,
                location_zone=location_zone,
                damage_description=damage_description,
                incident_date_approx=incident_date_approx,
                incident_time_window_start=incident_time_window_start,
                incident_time_window_end=incident_time_window_end,
                image_count=len(image_files) if image_files else 0,
                is_processed=False,
                updated_at=datetime.now(timezone.utc),
            )
            db.add(claim)
            await db.flush()
            
            logger.debug(f"Created claim record: {claim.id}")
            
            # Step 2: Process images
            image_embedding = None
            processed_images = []
            image_urls = None
            if image_files:
                image_embedding, processed_images = await ClaimProcessingService._process_images(
                    image_files
                )
                logger.debug(f"Processed {len(image_files)} images")

                stored_images = await ImageStorageService.persist_images(
                    db=db,
                    claim=claim,
                    image_payloads=image_files,
                    mask_images=True,
                )
                image_urls = [
                    ImageStorageService.create_signed_url(img.file_path)
                    for img in stored_images
                ]
                image_urls = [url for url in image_urls if url]
                if image_urls:
                    logger.debug(f"Gemini signed URLs: {image_urls}")
            
            # Step 3: Generate embeddings
            text_embedding = await EmbeddingService.generate_text_embedding(
                damage_description
            )
            
            if image_embedding is None:
                # If no images, use placeholder
                image_embedding = [0.5] * 128
            
            logger.debug("Generated embeddings")
            
            # Step 4: Generate fingerprints
            spatial_fp = FingerprintService.generate_spatial_fingerprint(location_zone)
            temporal_fp = FingerprintService.generate_temporal_fingerprint(
                incident_date_approx,
                incident_time_window_start,
                incident_time_window_end,
            )
            severity = FingerprintService.calculate_damage_severity_score(
                damage_description,
                len(image_files) if image_files else 0,
            )

            SupabaseMetadataService.upsert_claim_metadata(
                claim_reference_id=claim_reference_id,
                insurance_company_id=(user.organization_name or str(user.id)),
                incident_type=incident_type,
                incident_time=incident_time_window_start,
                incident_area=location_zone,
                severity_label=map_severity_label(severity),
            )
            
            logger.debug("Generated fingerprints")
            
            # Step 5: Find similar historical incidents
            similar_incidents = await SimilarityService.find_similar_incidents(
                db,
                text_embedding,
                image_embedding,
                spatial_fp,
                temporal_fp,
                incident_type,
                limit=10,
            )
            
            logger.info(f"Found {len(similar_incidents)} similar incidents for claim {claim_reference_id}")
            if similar_incidents:
                for idx, inc in enumerate(similar_incidents[:3]):  # Log top 3
                    logger.info(
                        f"  Match {idx+1}: {inc.get('claim_reference_id')} at {inc.get('organization_name')} - "
                        f"Overall: {inc.get('overall_similarity', 0):.1%}, "
                        f"Image: {inc.get('image_similarity', 0):.1%}, "
                        f"Text: {inc.get('text_similarity', 0):.1%}"
                    )
            
            # Step 6: Get AI-powered fraud analysis from Gemini
            temporal_score = (
                similar_incidents[0]["temporal_similarity"]
                if similar_incidents
                else 0.0
            )
            spatial_score = (
                similar_incidents[0]["spatial_similarity"]
                if similar_incidents
                else 0.0
            )
            
            gemini_analysis = await gemini_fraud_analyzer.analyze_claim_fraud_risk(
                incident_type=incident_type,
                damage_description=damage_description,
                location_zone=location_zone,
                image_analysis=None,
                image_bytes_list=processed_images,
                image_urls=image_urls,
                similar_incidents=similar_incidents,
                temporal_pattern_score=temporal_score,
                spatial_cluster_score=spatial_score,
            )
            
            # Use Gemini's analysis or fallback to heuristic
            fraud_risk_score = gemini_analysis.get("fraud_score", 0.0)
            fraud_risk_level = gemini_analysis.get("fraud_risk_level", "LOW")
            recommendation = ClaimProcessingService._map_recommendation(
                fraud_risk_level, fraud_risk_score
            )
            
            logger.debug(
                f"Gemini fraud risk: {fraud_risk_score:.2f} ({fraud_risk_level})"
            )
            
            # Step 7: Create incident fingerprint (PERSISTED FOR FUTURE COMPARISON)
            incident_fingerprint = IncidentFingerprint(
                claim_id=claim.id,
                claim_reference_id=claim_reference_id,
                image_embedding=image_embedding,
                text_embedding=text_embedding,
                spatial_fingerprint=spatial_fp,
                temporal_fingerprint=temporal_fp,
                incident_type_code=incident_type,
                damage_severity_score=severity,
                embedding_model_version="1.0",
            )
            db.add(incident_fingerprint)
            await db.flush()
            
            logger.debug(f"Created incident fingerprint: {incident_fingerprint.id}")
            
            # Step 8: Create fraud analysis result
            top_match = None
            if similar_incidents:
                match = similar_incidents[0]
                
                # Calculate days since matched incident (handle timezone)
                days_since = None
                if match["incident_date"]:
                    incident_date = match["incident_date"]
                    # Ensure incident_date is timezone-aware
                    if incident_date.tzinfo is None:
                        incident_date = incident_date.replace(tzinfo=timezone.utc)
                    days_since = (datetime.now(timezone.utc) - incident_date).days
                
                # Use data from similar_incidents which now includes company info
                # Convert datetime to ISO string for JSON serialization
                matched_date = match["incident_date"]
                matched_date_str = matched_date.isoformat() if matched_date else None
                
                top_match = {
                    "matched_fingerprint_id": match["fingerprint_id"],
                    "similarity_score": float(match["overall_similarity"]),
                    "matched_incident_type": match["incident_type"],
                    "matched_incident_date": matched_date_str,
                    "matched_claim_reference_id": match["claim_reference_id"],
                    "matched_organization_name": match["organization_name"],
                    "matched_location_zone": match["location_zone"],
                    "days_since_matched_incident": days_since,
                    "similarity_breakdown": {
                        "image_similarity": float(match["image_similarity"]),
                        "text_similarity": float(match["text_similarity"]),
                        "temporal_similarity": float(match["temporal_similarity"]),
                        "spatial_similarity": float(match["spatial_similarity"]),
                    },
                }
            
            analysis_result = FraudAnalysisResult(
                claim_id=claim.id,
                matched_fingerprint_id=top_match["matched_fingerprint_id"]
                if top_match
                else None,
                overall_fraud_risk_score=float(fraud_risk_score),
                fraud_risk_level=fraud_risk_level,
                recommendation=recommendation,
                image_similarity_score=(
                    float(similar_incidents[0]["image_similarity"])
                    if similar_incidents
                    else None
                ),
                text_similarity_score=(
                    float(similar_incidents[0]["text_similarity"])
                    if similar_incidents
                    else None
                ),
                temporal_similarity_score=(
                    float(similar_incidents[0]["temporal_similarity"])
                    if similar_incidents
                    else None
                ),
                spatial_similarity_score=(
                    float(similar_incidents[0]["spatial_similarity"])
                    if similar_incidents
                    else None
                ),
                matched_fingerprint_count=len(similar_incidents),
                top_match_details=top_match,
                similarity_breakdown=[
                    {
                        "fingerprint_id": inc["fingerprint_id"],
                        "overall_similarity": float(inc["overall_similarity"]),
                        "text_similarity": float(inc["text_similarity"]),
                        "image_similarity": float(inc["image_similarity"]),
                        "spatial_similarity": float(inc["spatial_similarity"]),
                        "temporal_similarity": float(inc["temporal_similarity"]),
                        "incident_type": inc["incident_type"],
                        "incident_date": inc["incident_date"].isoformat() if inc.get("incident_date") else None,
                        "claim_reference_id": inc["claim_reference_id"],
                        "organization_name": inc["organization_name"],
                        "location_zone": inc["location_zone"],
                    }
                    for inc in similar_incidents
                ],
                risk_factors=ClaimProcessingService._identify_risk_factors(
                    similar_incidents, severity, fraud_risk_score
                ),
                explanation=ClaimProcessingService._generate_explanation(
                    fraud_risk_score, fraud_risk_level, similar_incidents, severity
                ),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(analysis_result)
            
            # Update claim as processed
            claim.is_processed = True
            claim.processed_at = datetime.now(timezone.utc)
            db.add(claim)
            
            # Commit everything
            await db.commit()

            SupabaseMetadataService.mark_claim_processed(claim_reference_id)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Log audit trail
            audit_logger.info(
                f"Claim analyzed: {claim_reference_id}, "
                f"Risk Level: {fraud_risk_level}, "
                f"Score: {fraud_risk_score:.2f}, "
                f"User: {user.username}"
            )
            
            logger.info(f"Completed claim analysis: {claim_reference_id}")
            
            return {
                "claim_reference_id": claim_reference_id,
                "analysis_status": "completed",
                "fraud_risk_score": fraud_risk_score,
                "fraud_risk_level": fraud_risk_level,
                "recommendation": recommendation,
                "matched_incidents_count": len(similar_incidents),
                "top_match": top_match,
                "risk_factors": analysis_result.risk_factors,
                "explanation": analysis_result.explanation,
                "analyzed_at": datetime.now(timezone.utc),
                "processing_time_ms": processing_time_ms,
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error processing claim {claim_reference_id}: {e}", exc_info=True)
            audit_logger.error(f"Claim processing failed: {claim_reference_id}, Error: {str(e)}")
            raise

    @staticmethod
    async def _process_images(image_files: list) -> tuple[list, list]:
        """
        Process a list of images.
        
        NOTE: Raw images are stored in Supabase when configured.
        Only embeddings and fingerprints are stored permanently in the core DB.
        
        Args:
            image_files: List of image bytes
            
        Returns:
            Tuple of (image embedding vector, processed image bytes list)
        """
        if not image_files:
            return [0.5] * 128, []
        
        # Process each image: mask sensitive data, validate
        processed_embeddings = []
        
        processed_images = []
        for payload in image_files:
            image_bytes = payload.get("bytes") if isinstance(payload, dict) else payload
            if not isinstance(image_bytes, (bytes, bytearray)):
                continue
            # Validate image
            is_valid, error_msg = await ImageProcessingService.validate_image(image_bytes)
            if not is_valid:
                logger.warning(f"Image validation failed: {error_msg}")
                continue
            
            # Mask sensitive regions (placeholder)
            masked_image = await ImageProcessingService.mask_sensitive_regions(image_bytes)
            
            # Generate embedding
            embedding = await EmbeddingService.generate_image_embedding(masked_image)
            processed_embeddings.append(embedding)
            processed_images.append(masked_image)
        
        # Average embeddings if multiple images
        if processed_embeddings:
            import numpy as np
            avg_embedding = np.mean(processed_embeddings, axis=0).tolist()
            return avg_embedding, processed_images

        return [0.5] * 128, processed_images

    @staticmethod
    def _identify_risk_factors(
        similar_incidents: list,
        severity: float,
        fraud_risk_score: float
    ) -> list:
        """Identify and list fraud risk factors."""
        factors = []
        
        if not similar_incidents:
            factors.append("No similar historical incidents found")
            return factors
        
        if similar_incidents:
            best_match = similar_incidents[0]
            company_info = best_match.get("organization_name", "Unknown Company")
            
            factors.append(
                f"High similarity ({best_match['overall_similarity']:.0%}) to claim at {company_info} - "
                f"Image: {best_match['image_similarity']:.0%}"
            )
            
            if best_match["temporal_similarity"] > 0.8:
                factors.append(
                    f"Similar incident timing detected (match at {company_info})"
                )
            
            if best_match["spatial_similarity"] > 0.8:
                factors.append(
                    f"Similar location detected (match at {company_info})"
                )
        
        # Check for cross-company fraud
        unique_companies = set(
            inc.get("organization_name", "Unknown") 
            for inc in similar_incidents
        )
        if len(unique_companies) > 1:
            factors.append(
                f"CRITICAL: Similar claims found at {len(unique_companies)} different companies: "
                f"{', '.join(unique_companies)}"
            )
        
        if len(similar_incidents) > 2:
            factors.append(
                f"Multiple ({len(similar_incidents)}) similar historical incidents found"
            )
        
        if severity < 0.3 and similar_incidents:
            factors.append("Low damage severity but high similarity pattern")
        
        return factors

    @staticmethod
    def _map_recommendation(fraud_risk_level: str, fraud_risk_score: float) -> str:
        """Map risk level/score to a recommendation enum value."""
        level = (fraud_risk_level or "LOW").upper()

        if level in {"HIGH", "CRITICAL"}:
            return "INVESTIGATE"
        if level == "MEDIUM":
            return "HOLD"

        if fraud_risk_score >= 0.5:
            return "HOLD"
        return "PROCEED"

    @staticmethod
    def _generate_explanation(
        fraud_risk_score: float,
        fraud_risk_level: str,
        similar_incidents: list,
        severity: float,
    ) -> str:
        """Generate human-readable explanation of fraud assessment."""
        
        # Check for cross-company fraud
        unique_companies = set()
        company_details = ""
        if similar_incidents:
            unique_companies = set(
                inc.get("organization_name", "Unknown") 
                for inc in similar_incidents
            )
            if len(unique_companies) > 1:
                company_details = (
                    f" WARNING: Similar claims detected across {len(unique_companies)} "
                    f"different insurance companies ({', '.join(unique_companies)}). "
                    f"This is a major fraud indicator."
                )
            elif unique_companies:
                company_name = list(unique_companies)[0]
                company_details = f" Similar claim(s) found at {company_name}."
        
        if fraud_risk_level == "LOW":
            if not similar_incidents:
                return (
                    "Claim shows low fraud risk. No similar historical incidents found "
                    "across any insurance company. Standard verification procedures recommended."
                )
            return (
                f"Claim shows low fraud risk. No significant matches to historical "
                f"incidents.{company_details} Recommend approval with standard processing."
            )
        elif fraud_risk_level == "MEDIUM":
            return (
                f"Claim shows medium fraud risk ({fraud_risk_score:.0%}). "
                f"Found {len(similar_incidents)} similar historical incident(s).{company_details} "
                "Recommend standard verification procedures."
            )
        elif fraud_risk_level == "HIGH":
            return (
                f"Claim shows high fraud risk ({fraud_risk_score:.0%}). "
                f"Significant similarity to {len(similar_incidents)} historical incident(s).{company_details} "
                "Recommend detailed investigation and verification."
            )
        else:  # CRITICAL
            return (
                f"Claim shows CRITICAL fraud risk ({fraud_risk_score:.0%}). "
                f"Multiple matches to historical incidents.{company_details} "
                "Recommend immediate investigation and potential fraud referral."
            )
