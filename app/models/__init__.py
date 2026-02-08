"""
SQLAlchemy ORM models for CrossInsure AI.

Core models include:
- User: System users with role-based access
- Claim: Insurance claim submissions
- IncidentFingerprint: Anonymized incident fingerprints (persisted forever)
- FraudAnalysisResult: Fraud analysis results and similarity scores
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    JSON,
    LargeBinary,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration for role-based access control."""
    ADMIN = "ADMIN"
    INSURER = "INSURER"


class FraudRiskLevel(str, enum.Enum):
    """Fraud risk level classification."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FraudRecommendation(str, enum.Enum):
    """Recommendation for claim handling."""
    PROCEED = "PROCEED"
    HOLD = "HOLD"
    INVESTIGATE = "INVESTIGATE"


class User(Base):
    """
    User model representing system users (insurers and admins).
    
    Raw personal data is NOT stored beyond authentication.
    Only essential identification is retained.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.INSURER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Organization info (minimal, for audit purposes)
    organization_name = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    claims = relationship("Claim", back_populates="submitted_by")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class Claim(Base):
    """
    Claim model representing insurance claim submissions.
    
    Design principle: Raw images and personal details are NOT persisted.
    Only anonymized processing outputs are stored in IncidentFingerprint.
    """
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    
    # Reference and metadata
    claim_reference_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Claim details (anonymized)
    incident_type = Column(String(255), nullable=False)  # e.g., "motor_damage", "property_damage"
    location_zone = Column(String(255), nullable=False)  # Generalized zone, not exact address
    damage_description = Column(Text, nullable=False)
    
    # Temporal information (generalized)
    incident_date_approx = Column(DateTime(timezone=True), nullable=False)
    incident_time_window_start = Column(DateTime(timezone=True), nullable=False)
    incident_time_window_end = Column(DateTime(timezone=True), nullable=False)
    
    # Processing metadata
    image_count = Column(Integer, default=0, nullable=False)
    is_processed = Column(Boolean, default=False, nullable=False)
    processing_error = Column(Text, nullable=True)
    
    # Timestamps
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=False)

    # Relationships
    submitted_by = relationship("User", back_populates="claims")
    fingerprint = relationship("IncidentFingerprint", back_populates="claim", uselist=False)
    analysis_results = relationship("FraudAnalysisResult", back_populates="claim")
    images = relationship("ClaimImage", back_populates="claim")

    def __repr__(self):
        return f"<Claim(id={self.id}, reference_id={self.claim_reference_id})>"


class IncidentFingerprint(Base):
    """
    Anonymized incident fingerprint - the ONLY persistent record of an incident.
    
    This is the core of the fraud detection system:
    - Stores only embeddings and fingerprints
    - NO raw images
    - NO personal identifiers
    - NO policy numbers or vehicle registration
    - Persists indefinitely to compare against future claims
    
    Used for: Cross-policy fraud detection across all insurers
    """
    __tablename__ = "incident_fingerprints"

    id = Column(Integer, primary_key=True, index=True)
    
    # Reference to the original claim (can be anonymized/cleared later)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False, index=True)
    claim_reference_id = Column(String(255), unique=True, index=True, nullable=False)
    
    # AI-Generated Embeddings (stored for similarity comparisons)
    # Using JSON to store vector embeddings (typically numpy arrays serialized)
    image_embedding = Column(JSON, nullable=False)  # Vector embedding from damage images
    text_embedding = Column(JSON, nullable=False)   # Vector embedding from damage description
    
    # Spatio-Temporal Fingerprint
    # Compact representation of: location, time, damage type, severity pattern
    spatial_fingerprint = Column(String(255), nullable=False, index=True)  # Location hash
    temporal_fingerprint = Column(String(255), nullable=False, index=True) # Time window hash
    incident_type_code = Column(String(50), nullable=False, index=True)   # Incident classification
    
    # Damage severity indicator (anonymized scale)
    damage_severity_score = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Metadata
    embedding_model_version = Column(String(50), default="1.0", nullable=False)
    
    # Timestamps
    stored_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    claim = relationship("Claim", back_populates="fingerprint")
    similarity_matches = relationship("FraudAnalysisResult", back_populates="matched_fingerprint")

    def __repr__(self):
        return f"<IncidentFingerprint(id={self.id}, claim_ref={self.claim_reference_id})>"


class FraudAnalysisResult(Base):
    """
    Results of fraud analysis for a claim comparison.
    
    Stores:
    - Fraud risk assessment
    - Similarity breakdowns (temporal, spatial, image, text)
    - Comparison details with historical incidents
    - Recommendations for claim handling
    """
    __tablename__ = "fraud_analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    
    # Reference to the analyzed claim
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False, index=True)
    
    # Reference to matched historical incident (if found)
    matched_fingerprint_id = Column(Integer, ForeignKey("incident_fingerprints.id"), nullable=True)
    
    # Fraud Risk Scoring
    overall_fraud_risk_score = Column(Float, nullable=False)  # 0.0 to 1.0
    fraud_risk_level = Column(Enum(FraudRiskLevel), nullable=False)
    recommendation = Column(Enum(FraudRecommendation), nullable=False)
    
    # Similarity Breakdown
    image_similarity_score = Column(Float, nullable=True)     # 0.0 to 1.0
    text_similarity_score = Column(Float, nullable=True)      # 0.0 to 1.0
    temporal_similarity_score = Column(Float, nullable=True)  # 0.0 to 1.0
    spatial_similarity_score = Column(Float, nullable=True)   # 0.0 to 1.0
    
    # Detailed Results
    matched_fingerprint_count = Column(Integer, default=0, nullable=False)
    top_match_details = Column(JSON, nullable=True)  # Details of top matching incident
    similarity_breakdown = Column(JSON, nullable=True)  # Full breakdown of all matches
    
    # Explanation/Justification
    risk_factors = Column(JSON, nullable=True)  # Array of identified risk factors
    explanation = Column(Text, nullable=True)  # Human-readable explanation
    
    # Analyst notes (for investigations)
    analyst_notes = Column(Text, nullable=True)
    reviewed_by_admin = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=False)

    # Relationships
    claim = relationship("Claim", back_populates="analysis_results")
    matched_fingerprint = relationship("IncidentFingerprint", back_populates="similarity_matches")

    def __repr__(self):
        return f"<FraudAnalysisResult(id={self.id}, risk_level={self.fraud_risk_level})>"


class ClaimImage(Base):
    """
    Persisted claim image metadata.
    
    Image bytes are stored in a secure blob store (filesystem) and referenced here.
    """
    __tablename__ = "claim_images"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False, index=True)

    original_filename = Column(String(255), nullable=True)
    content_type = Column(String(100), nullable=True)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    is_masked = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    claim = relationship("Claim", back_populates="images")

    def __repr__(self):
        return f"<ClaimImage(id={self.id}, claim_id={self.claim_id})>"
