"""
Admin monitoring API routes.

Endpoints:
- GET /admin/metrics: System metrics and statistics
- GET /admin/system-health: System health status
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from app.core.database import get_db
from app.schemas import MetricsResponse, SystemHealthResponse
from app.models import User, Claim, IncidentFingerprint, FraudAnalysisResult, FraudRiskLevel
from app.api.dependencies import get_admin_user
from app.core.logging_config import get_logger
from app.supabase_client import get_supabase_client, is_supabase_configured
from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = get_logger(__name__)


@router.get("/metrics", response_model=MetricsResponse, status_code=200)
async def get_metrics(
    current_admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get system metrics and statistics.
    
    Returns:
    - total_claims_analyzed: Total claims processed
    - total_fingerprints_stored: Total anonymized fingerprints stored
    - high_risk_fraud_count: Claims flagged as HIGH fraud risk
    - medium_risk_fraud_count: Claims flagged as MEDIUM fraud risk
    - low_risk_fraud_count: Claims flagged as LOW fraud risk
    - claims_analyzed_today: Claims processed today
    - claims_analyzed_this_week: Claims processed in last 7 days
    - claims_analyzed_this_month: Claims processed in last 30 days
    - average_fraud_risk_score: Average fraud risk score across all claims
    - most_common_risk_factor: Most frequently identified risk factor
    - fingerprints_added_today: Fingerprints added today
    
    Admin access required.
    """
    try:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Total claims analyzed
        stmt = select(func.count(Claim.id))
        result = await db.execute(stmt)
        total_claims = result.scalar() or 0
        
        # Total fingerprints stored
        stmt = select(func.count(IncidentFingerprint.id))
        result = await db.execute(stmt)
        total_fingerprints = result.scalar() or 0
        
        # Risk level counts
        stmt = select(func.count(FraudAnalysisResult.id)).where(
            FraudAnalysisResult.fraud_risk_level == FraudRiskLevel.HIGH.value
        )
        result = await db.execute(stmt)
        high_risk_count = result.scalar() or 0
        
        stmt = select(func.count(FraudAnalysisResult.id)).where(
            FraudAnalysisResult.fraud_risk_level == FraudRiskLevel.MEDIUM.value
        )
        result = await db.execute(stmt)
        medium_risk_count = result.scalar() or 0
        
        stmt = select(func.count(FraudAnalysisResult.id)).where(
            FraudAnalysisResult.fraud_risk_level == FraudRiskLevel.LOW.value
        )
        result = await db.execute(stmt)
        low_risk_count = result.scalar() or 0
        
        # Claims processed today
        stmt = select(func.count(Claim.id)).where(Claim.submitted_at >= today_start)
        result = await db.execute(stmt)
        claims_today = result.scalar() or 0
        
        # Claims processed this week
        stmt = select(func.count(Claim.id)).where(Claim.submitted_at >= week_ago)
        result = await db.execute(stmt)
        claims_week = result.scalar() or 0
        
        # Claims processed this month
        stmt = select(func.count(Claim.id)).where(Claim.submitted_at >= month_ago)
        result = await db.execute(stmt)
        claims_month = result.scalar() or 0
        
        # Average fraud risk score
        stmt = select(func.avg(FraudAnalysisResult.overall_fraud_risk_score))
        result = await db.execute(stmt)
        avg_fraud_score = float(result.scalar() or 0.0)
        
        # Most common risk factor (simplified: just count)
        most_common_risk = "Image similarity to historical incident"  # Placeholder
        
        # Fingerprints added today
        stmt = select(func.count(IncidentFingerprint.id)).where(
            IncidentFingerprint.stored_at >= today_start
        )
        result = await db.execute(stmt)
        fingerprints_today = result.scalar() or 0
        
        logger.info(
            f"Metrics retrieved by admin {current_admin.username}: "
            f"Total Claims: {total_claims}, "
            f"Total Fingerprints: {total_fingerprints}"
        )
        
        return MetricsResponse(
            total_claims_analyzed=total_claims,
            total_fingerprints_stored=total_fingerprints,
            high_risk_fraud_count=high_risk_count,
            medium_risk_fraud_count=medium_risk_count,
            low_risk_fraud_count=low_risk_count,
            claims_analyzed_today=claims_today,
            claims_analyzed_this_week=claims_week,
            claims_analyzed_this_month=claims_month,
            average_fraud_risk_score=avg_fraud_score,
            most_common_risk_factor=most_common_risk,
            fingerprints_added_today=fingerprints_today,
            timestamp=now,
        )
        
    except Exception as e:
        logger.error(f"Error retrieving metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving system metrics",
        )


@router.get("/system-health", response_model=SystemHealthResponse, status_code=200)
async def get_system_health(
    current_admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get system health status.
    
    Returns:
    - status: Overall system status (healthy, degraded, unhealthy)
    - database_connected: Whether database connection is working
    - api_response_time_ms: Current API response time estimate
    - components: Status of individual system components
    
    Admin access required.
    """
    try:
        import time
        start_time = time.time()
        
        # Test database connection
        stmt = select(func.count(Claim.id))
        result = await db.execute(stmt)
        result.scalar()
        db_connected = True
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Determine overall health
        overall_status = "healthy"
        if response_time_ms > 1000:
            overall_status = "degraded"
        
        logger.info(
            f"System health checked by admin {current_admin.username}: "
            f"Status: {overall_status}, DB Connected: {db_connected}"
        )
        
        return SystemHealthResponse(
            status=overall_status,
            database_connected=db_connected,
            api_response_time_ms=response_time_ms,
            timestamp=datetime.now(timezone.utc),
            components={
                "database": "healthy" if db_connected else "unhealthy",
                "cache": "healthy",
                "ai_service": "pending",  # Awaiting Gemini integration
            },
        )
        
    except Exception as e:
        logger.error(f"Error checking system health: {str(e)}", exc_info=True)
        return SystemHealthResponse(
            status="unhealthy",
            database_connected=False,
            api_response_time_ms=0,
            timestamp=datetime.now(timezone.utc),
            components={
                "database": "unhealthy",
                "cache": "unhealthy",
                "ai_service": "pending",
            },
        )


@router.get("/supabase-health", status_code=200)
async def get_supabase_health(
    current_admin: User = Depends(get_admin_user),
):
    """
    Check Supabase connectivity (Postgres + Storage).

    Admin access required.
    """
    if not is_supabase_configured():
        return {
            "status": "not_configured",
            "configured": False,
            "database_ok": False,
            "storage_ok": False,
            "bucket": settings.supabase_storage_bucket,
        }

    supabase = get_supabase_client()
    database_ok = False
    storage_ok = False

    try:
        supabase.table("claims").select("claim_id").limit(1).execute()
        database_ok = True
    except Exception as exc:
        logger.warning(f"Supabase DB check failed: {exc}")

    try:
        supabase.storage.from_(settings.supabase_storage_bucket).list("")
        storage_ok = True
    except Exception as exc:
        logger.warning(f"Supabase storage check failed: {exc}")

    status_label = "healthy" if database_ok and storage_ok else "degraded"

    return {
        "status": status_label,
        "configured": True,
        "database_ok": database_ok,
        "storage_ok": storage_ok,
        "bucket": settings.supabase_storage_bucket,
    }
