"""
Supabase metadata sync service.

Keeps a lightweight metadata mirror in Supabase Postgres.
"""

from datetime import datetime
from typing import Optional
from app.core.logging_config import get_logger
from app.supabase_client import get_supabase_client, is_supabase_configured

logger = get_logger(__name__)


class SupabaseMetadataService:
    """Best-effort metadata sync to Supabase."""

    @staticmethod
    def upsert_claim_metadata(
        claim_reference_id: str,
        insurance_company_id: str,
        incident_type: str,
        incident_time: datetime,
        incident_area: str,
        severity_label: str,
    ) -> None:
        if not is_supabase_configured():
            return

        supabase = get_supabase_client()
        payload = {
            "claim_id": claim_reference_id,
            "insurance_company_id": insurance_company_id,
            "incident_type": incident_type,
            "incident_time": incident_time.isoformat(),
            "incident_area": incident_area,
            "severity": severity_label,
            "ai_processed": False,
        }

        try:
            supabase.table("claims").upsert(payload).execute()
        except Exception as exc:
            logger.warning(f"Supabase claim upsert failed: {exc}")

    @staticmethod
    def mark_claim_processed(claim_reference_id: str) -> None:
        if not is_supabase_configured():
            return

        supabase = get_supabase_client()
        try:
            supabase.table("claims").update({"ai_processed": True}).eq(
                "claim_id", claim_reference_id
            ).execute()
        except Exception as exc:
            logger.warning(f"Supabase claim update failed: {exc}")

    @staticmethod
    def insert_claim_image_metadata(
        claim_reference_id: str,
        image_path: str,
        image_hash: str,
    ) -> None:
        if not is_supabase_configured():
            return

        supabase = get_supabase_client()
        payload = {
            "claim_id": claim_reference_id,
            "image_path": image_path,
            "image_hash": image_hash,
        }

        try:
            supabase.table("claim_images").insert(payload).execute()
        except Exception as exc:
            logger.warning(f"Supabase claim image insert failed: {exc}")


def map_severity_label(score: float) -> str:
    if score < 0.3:
        return "LOW"
    if score < 0.7:
        return "MEDIUM"
    return "HIGH"
