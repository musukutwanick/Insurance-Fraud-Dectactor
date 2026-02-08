"""
Pydantic schemas for request/response validation.

Organized by feature:
- Authentication
- Claims submission and analysis
- Admin monitoring
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# Authentication Schemas
# ============================================================================

class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "ADMIN"
    INSURER = "INSURER"


class UserLoginRequest(BaseModel):
    """Request schema for user login."""
    username: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8)

    class Config:
        example = {
            "username": "insurer_user",
            "password": "secure_password_123",
        }


class DemoLoginRequest(BaseModel):
    """Request schema for demo auto-login without a password."""
    company_name: str = Field(..., min_length=2, max_length=255)
    username: Optional[str] = Field(None, min_length=3, max_length=255)

    class Config:
        example = {
            "company_name": "Alpha Insurance",
            "username": "alpha_insurance_demo",
        }


class TokenResponse(BaseModel):
    """Response schema for authentication token."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

    class Config:
        example = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 1800,
        }


class RefreshTokenRequest(BaseModel):
    """Request schema for refreshing authentication token."""
    refresh_token: str = Field(...)

    class Config:
        example = {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        }


class UserResponse(BaseModel):
    """Response schema for user information."""
    id: int
    username: str
    email: str
    role: UserRole
    organization_name: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True
        example = {
            "id": 1,
            "username": "insurer_user",
            "email": "user@insurer.com",
            "role": "INSURER",
            "organization_name": "ABC Insurance",
            "is_active": True,
            "created_at": "2024-01-20T10:00:00Z",
            "last_login": "2024-01-31T15:30:00Z",
        }


# ============================================================================
# Claims Submission Schemas
# ============================================================================

class IncidentType(str, Enum):
    """Types of incidents."""
    MOTOR_DAMAGE = "motor_damage"
    COLLISION = "collision"
    THEFT = "theft"
    PROPERTY_DAMAGE = "property_damage"
    FIRE = "fire"
    WATER_DAMAGE = "water_damage"
    OTHER = "other"


class LocationZone(str, Enum):
    """Generalized location zones (anonymized)."""
    ZONE_A = "zone_a"
    ZONE_B = "zone_b"
    ZONE_C = "zone_c"
    ZONE_D = "zone_d"
    ZONE_E = "zone_e"


class ClaimSubmissionRequest(BaseModel):
    """Request schema for claim submission and analysis."""
    incident_type: IncidentType = Field(..., description="Type of incident")
    damage_description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Detailed description of damage"
    )
    location_zone: LocationZone = Field(..., description="Generalized location zone")
    incident_date_approx: datetime = Field(..., description="Approximate incident date")
    incident_time_window_start: datetime = Field(..., description="Start of estimated incident time window")
    incident_time_window_end: datetime = Field(..., description="End of estimated incident time window")

    @validator("incident_time_window_end")
    def validate_time_window(cls, v, values):
        """Ensure time window end is after start."""
        if "incident_time_window_start" in values and v <= values["incident_time_window_start"]:
            raise ValueError("Time window end must be after time window start")
        return v

    class Config:
        example = {
            "incident_type": "motor_damage",
            "damage_description": "Vehicle collided with another car at intersection. Significant front-end damage.",
            "location_zone": "zone_a",
            "incident_date_approx": "2024-01-30T14:00:00Z",
            "incident_time_window_start": "2024-01-30T13:00:00Z",
            "incident_time_window_end": "2024-01-30T15:00:00Z",
        }


class SimilarityBreakdown(BaseModel):
    """Breakdown of similarity scores across different dimensions."""
    image_similarity: Optional[float] = Field(None, ge=0.0, le=1.0, description="Image similarity score")
    text_similarity: Optional[float] = Field(None, ge=0.0, le=1.0, description="Text/description similarity")
    temporal_similarity: Optional[float] = Field(None, ge=0.0, le=1.0, description="Temporal (time) similarity")
    spatial_similarity: Optional[float] = Field(None, ge=0.0, le=1.0, description="Spatial (location) similarity")

    class Config:
        example = {
            "image_similarity": 0.87,
            "text_similarity": 0.72,
            "temporal_similarity": 0.91,
            "spatial_similarity": 0.85,
        }


class TopMatchDetails(BaseModel):
    """Details of the top fraud match found."""
    matched_fingerprint_id: int
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    matched_incident_type: str
    matched_incident_date: datetime
    days_since_matched_incident: int
    similarity_breakdown: SimilarityBreakdown

    class Config:
        from_attributes = True
        example = {
            "matched_fingerprint_id": 15,
            "similarity_score": 0.86,
            "matched_incident_type": "motor_damage",
            "matched_incident_date": "2023-12-15T14:30:00Z",
            "days_since_matched_incident": 47,
            "similarity_breakdown": {
                "image_similarity": 0.87,
                "text_similarity": 0.72,
                "temporal_similarity": 0.91,
                "spatial_similarity": 0.85,
            }
        }


class FraudRiskLevel(str, Enum):
    """Fraud risk level classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FraudRecommendation(str, Enum):
    """Recommendation for claim handling."""
    PROCEED = "PROCEED"
    HOLD = "HOLD"
    INVESTIGATE = "INVESTIGATE"


class ClaimAnalysisResponse(BaseModel):
    """Response schema for claim analysis results."""
    claim_reference_id: str = Field(..., description="Unique anonymized claim reference ID")
    analysis_status: str = Field(..., description="Processing status")
    fraud_risk_score: float = Field(..., ge=0.0, le=1.0, description="Overall fraud risk (0.0=low, 1.0=critical)")
    fraud_risk_level: FraudRiskLevel = Field(..., description="Risk level classification")
    recommendation: FraudRecommendation = Field(..., description="Recommended action")
    
    # Similarity Results
    matched_incidents_count: int = Field(..., description="Number of matching historical incidents found")
    top_match: Optional[TopMatchDetails] = Field(None, description="Most similar historical incident")
    
    # Risk Factors
    risk_factors: List[str] = Field(default_factory=list, description="Identified fraud risk factors")
    explanation: str = Field(..., description="Human-readable explanation of fraud assessment")
    
    # Metadata
    analyzed_at: datetime
    processing_time_ms: int = Field(..., description="Time taken to analyze claim in milliseconds")

    class Config:
        from_attributes = True
        example = {
            "claim_reference_id": "CLM-8f92c7d3-2e1a-4b8c-9d5f",
            "analysis_status": "completed",
            "fraud_risk_score": 0.72,
            "fraud_risk_level": "HIGH",
            "recommendation": "INVESTIGATE",
            "matched_incidents_count": 3,
            "top_match": {
                "matched_fingerprint_id": 15,
                "similarity_score": 0.86,
                "matched_incident_type": "motor_damage",
                "matched_incident_date": "2023-12-15T14:30:00Z",
                "days_since_matched_incident": 47,
                "similarity_breakdown": {
                    "image_similarity": 0.87,
                    "text_similarity": 0.72,
                    "temporal_similarity": 0.91,
                    "spatial_similarity": 0.85,
                }
            },
            "risk_factors": [
                "High image similarity to incident from 47 days ago",
                "Location and time pattern matches previous claim",
                "Damage description contains common fraud indicators"
            ],
            "explanation": "Claim shows elevated fraud risk due to high similarity to a previous claim. Recommend investigation.",
            "analyzed_at": "2024-01-31T16:45:30Z",
            "processing_time_ms": 2340,
        }


# ============================================================================
# Admin Monitoring Schemas
# ============================================================================

class SystemHealthResponse(BaseModel):
    """Response schema for system health monitoring."""
    status: str = Field(..., description="Overall system status")
    database_connected: bool
    api_response_time_ms: int
    timestamp: datetime
    
    # Component health
    components: Dict[str, str] = Field(default_factory=dict)

    class Config:
        example = {
            "status": "healthy",
            "database_connected": True,
            "api_response_time_ms": 45,
            "timestamp": "2024-01-31T16:50:00Z",
            "components": {
                "database": "healthy",
                "cache": "healthy",
                "ai_service": "pending",
            }
        }


class MetricsResponse(BaseModel):
    """Response schema for system metrics."""
    total_claims_analyzed: int
    total_fingerprints_stored: int
    high_risk_fraud_count: int
    medium_risk_fraud_count: int
    low_risk_fraud_count: int
    
    # Time-based metrics
    claims_analyzed_today: int
    claims_analyzed_this_week: int
    claims_analyzed_this_month: int
    
    # Accuracy metrics
    average_fraud_risk_score: float
    most_common_risk_factor: Optional[str]
    
    # Storage metrics
    fingerprints_added_today: int
    
    timestamp: datetime

    class Config:
        example = {
            "total_claims_analyzed": 1250,
            "total_fingerprints_stored": 1189,
            "high_risk_fraud_count": 145,
            "medium_risk_fraud_count": 287,
            "low_risk_fraud_count": 818,
            "claims_analyzed_today": 23,
            "claims_analyzed_this_week": 156,
            "claims_analyzed_this_month": 487,
            "average_fraud_risk_score": 0.38,
            "most_common_risk_factor": "Image similarity to historical incident",
            "fingerprints_added_today": 20,
            "timestamp": "2024-01-31T16:50:00Z",
        }


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        example = {
            "error_code": "VALIDATION_ERROR",
            "message": "Invalid claim submission",
            "details": {
                "field": "incident_time_window_end",
                "reason": "End time must be after start time"
            },
            "timestamp": "2024-01-31T16:50:00Z",
        }
