"""
Claims API routes.

Endpoints:
- POST /claims/analyze: Submit claim and perform fraud analysis
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
)
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional, List
from app.core.database import get_db
from app.schemas import (
    ClaimSubmissionRequest,
    ClaimAnalysisResponse,
    IncidentType,
    LocationZone,
)
from app.models import User
from app.services.claim_service import ClaimProcessingService
from app.api.dependencies import get_current_user, oauth2_scheme
from app.core.logging_config import get_logger
from fastapi.security import HTTPBearer

router = APIRouter(prefix="/claims", tags=["Claims"])
logger = get_logger(__name__)
http_bearer = HTTPBearer()


@router.post("/analyze", response_model=ClaimAnalysisResponse, status_code=200)
async def analyze_claim(
    incident_type: str = Form(..., description="Type of incident"),
    damage_description: str = Form(..., description="Damage description"),
    location_zone: str = Form(..., description="Location zone"),
    incident_date_approx: str = Form(..., description="Approximate incident date (ISO format)"),
    incident_time_window_start: str = Form(..., description="Time window start (ISO format)"),
    incident_time_window_end: str = Form(..., description="Time window end (ISO format)"),
    damage_images: List[UploadFile] = File(default=[]),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a claim and perform AI-powered fraud analysis.
    
    This endpoint:
    1. Validates claim data
    2. Processes damage images (masking sensitive regions)
    3. Generates image and text embeddings
    4. Creates spatio-temporal fingerprint
    5. Compares against historical incidents
    6. Calculates fraud risk score
    7. Returns recommendation (PROCEED, HOLD, INVESTIGATE)
    
    Key architectural principle:
    - Raw images are stored in Supabase when configured
    - Only anonymized embeddings and fingerprints are persisted in the core DB
    - This allows comparison of future claims against historical patterns
    
    Request (multipart form):
    - incident_type: motor_damage, collision, theft, property_damage, fire, water_damage, other
    - damage_description: Detailed description of damage (min 10 chars)
    - location_zone: zone_a, zone_b, zone_c, zone_d, zone_e
    - incident_date_approx: ISO datetime string
    - incident_time_window_start: ISO datetime string
    - incident_time_window_end: ISO datetime string
    - damage_images: (optional) Upload 1-5 damage images
    
    Authorization:
    - Bearer token required (JWT from /auth/login)
    
    Returns:
    - claim_reference_id: Anonymized claim ID for tracking
    - fraud_risk_score: 0.0-1.0 (higher = more fraudulent)
    - fraud_risk_level: LOW, MEDIUM, HIGH, CRITICAL
    - recommendation: PROCEED, HOLD, INVESTIGATE
    - matched_incidents_count: Number of similar historical incidents
    - top_match: Details of most similar incident (if found)
    - risk_factors: List of identified risk indicators
    - explanation: Human-readable assessment
    - processing_time_ms: Analysis duration
    """
    try:
        # Authenticate user
        current_user = await get_current_user(token, db)
        
        logger.info(f"Claim analysis requested by user: {current_user.username}")
        
        # Validate and parse enum values
        try:
            incident_type_enum = IncidentType(incident_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid incident_type. Must be one of: {', '.join([e.value for e in IncidentType])}",
            )
        
        try:
            location_zone_enum = LocationZone(location_zone)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid location_zone. Must be one of: {', '.join([e.value for e in LocationZone])}",
            )
        
        # Parse datetime strings
        try:
            incident_date = datetime.fromisoformat(incident_date_approx)
            time_window_start = datetime.fromisoformat(incident_time_window_start)
            time_window_end = datetime.fromisoformat(incident_time_window_end)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid datetime format. Use ISO format (e.g., 2024-01-31T14:00:00). Error: {str(e)}",
            )
        
        # Validate time window
        if time_window_end <= time_window_start:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Time window end must be after time window start",
            )
        
        # Process images if provided
        image_payloads = None
        if damage_images:
            if len(damage_images) > 5:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Maximum 5 images allowed per claim",
                )
            
            image_payloads = []
            for img_file in damage_images:
                try:
                    image_content = await img_file.read()
                    image_payloads.append(
                        {
                            "bytes": image_content,
                            "filename": img_file.filename,
                            "content_type": img_file.content_type,
                        }
                    )
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Error reading image file: {str(e)}",
                    )
        
        # Process claim and perform fraud analysis
        analysis_result = await ClaimProcessingService.submit_and_analyze_claim(
            db=db,
            user=current_user,
            incident_type=incident_type_enum.value,
            damage_description=damage_description,
            location_zone=location_zone_enum.value,
            incident_date_approx=incident_date,
            incident_time_window_start=time_window_start,
            incident_time_window_end=time_window_end,
            image_files=image_payloads,
        )
        
        logger.info(
            f"Claim analysis completed: {analysis_result['claim_reference_id']}, "
            f"Risk Level: {analysis_result['fraud_risk_level']}"
        )
        
        return ClaimAnalysisResponse(**analysis_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during claim analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while analyzing the claim. Please try again later.",
        )
