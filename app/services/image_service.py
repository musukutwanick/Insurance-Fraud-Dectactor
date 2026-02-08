"""
Service layer for image processing.

Handles:
- Image masking (number plates, faces, sensitive regions)
- Image fingerprinting (perceptual hashing)
- Image preprocessing for embedding generation

NOTE: Raw images are stored in Supabase when configured; otherwise only local
metadata and embeddings are persisted.
"""

import hashlib
import os
import uuid
import asyncio
import numpy as np
from PIL import Image
import io
from typing import Tuple, List, Dict, Optional
from app.core.config import settings
from app.models import Claim, ClaimImage
from app.supabase_client import get_supabase_client, is_supabase_configured
from app.services.supabase_service import SupabaseMetadataService


class ImageProcessingService:
    """Service for processing and securing image data."""

    @staticmethod
    async def mask_sensitive_regions(image_bytes: bytes) -> bytes:
        """
        Mask sensitive regions in an image (number plates, faces, etc).
        
        This is a placeholder implementation. In production, use:
        - YOLOv8 or similar for object detection
        - MediaPipe for face detection
        - Custom ML models trained on vehicle registration plates
        
        Current implementation: Returns original bytes (placeholder)
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Processed image bytes with sensitive regions masked
        """
        # Placeholder: In production, implement:
        # 1. Load image from bytes
        # 2. Run face detection (MediaPipe)
        # 3. Run license plate detection (custom YOLO model)
        # 4. Apply Gaussian blur/pixelation to detected regions
        # 5. Return masked image bytes
        
        # For now, return original (to be replaced with actual implementation)
        return image_bytes

    @staticmethod
    async def generate_image_fingerprint(image_bytes: bytes) -> str:
        """
        Generate a perceptual fingerprint of the image.
        
        Uses:
        - Perceptual hashing (phash) for duplicate detection
        - Allows finding similar images even after compression/rotation
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Hex string representing the image fingerprint
        """
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Resize to standard size for consistent hashing
            image = image.resize((8, 8), Image.LANCZOS)
            
            # Convert to grayscale
            image = image.convert("L")
            
            # Get pixel values
            pixels = np.array(image)
            
            # Calculate average pixel value
            avg = pixels.mean()
            
            # Create hash: 1 if pixel > avg, 0 otherwise
            phash_bits = (pixels > avg).flatten()
            
            # Convert to hex string
            phash_hex = hex(int(''.join(phash_bits.astype(int).astype(str)), 2))
            
            return phash_hex
        except Exception as e:
            # On error, generate hash of raw bytes
            return hashlib.sha256(image_bytes).hexdigest()

    @staticmethod
    async def extract_image_metadata(image_bytes: bytes) -> dict:
        """
        Extract technical metadata from image (resolution, format, etc).
        
        Returns only technical data, never personal information.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Dictionary with image metadata
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            return {
                "format": image.format,
                "width": image.width,
                "height": image.height,
                "mode": image.mode,
                "size_bytes": len(image_bytes),
            }
        except Exception:
            return {
                "format": "unknown",
                "width": 0,
                "height": 0,
                "mode": "unknown",
                "size_bytes": len(image_bytes),
            }

    @staticmethod
    async def validate_image(image_bytes: bytes) -> Tuple[bool, str]:
        """
        Validate image format and size.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check size (max 10 MB)
        if len(image_bytes) > 10 * 1024 * 1024:
            return False, "Image exceeds maximum size of 10 MB"
        
        # Check format
        try:
            image = Image.open(io.BytesIO(image_bytes))
            allowed_formats = {"JPEG", "PNG", "TIFF", "BMP"}
            if image.format not in allowed_formats:
                return False, f"Image format {image.format} not supported"
            return True, ""
        except Exception as e:
            return False, f"Invalid image format: {str(e)}"


class ImageStorageService:
    """Service for persisting claim images to a secure blob store."""

    @staticmethod
    async def persist_images(
        db,
        claim: Claim,
        image_payloads: List[Dict[str, object]],
        mask_images: bool = True,
    ) -> List[ClaimImage]:
        if not image_payloads:
            return []

        use_supabase = is_supabase_configured()
        claim_dir = None
        if not use_supabase:
            storage_root = settings.image_storage_path
            claim_dir = os.path.join(storage_root, claim.claim_reference_id)
            os.makedirs(claim_dir, exist_ok=True)

        stored_images: List[ClaimImage] = []

        for payload in image_payloads:
            image_bytes = payload.get("bytes")
            if not isinstance(image_bytes, (bytes, bytearray)):
                continue

            content_type = payload.get("content_type") or "application/octet-stream"
            original_filename = payload.get("filename")

            is_valid, error_msg = await ImageProcessingService.validate_image(image_bytes)
            if not is_valid:
                continue

            if mask_images:
                image_bytes = await ImageProcessingService.mask_sensitive_regions(image_bytes)

            file_ext = ImageStorageService._infer_extension(content_type, original_filename)
            stored_name = f"{uuid.uuid4().hex}{file_ext}"
            if use_supabase:
                stored_path = ImageStorageService._build_object_path(
                    claim_reference_id=claim.claim_reference_id,
                    user_id=claim.user_id,
                    filename=stored_name,
                )
                await ImageStorageService._upload_to_supabase(
                    object_path=stored_path,
                    image_bytes=image_bytes,
                    content_type=content_type,
                )
            else:
                stored_path = os.path.join(claim_dir, stored_name)
                await asyncio.to_thread(
                    ImageStorageService._write_file, stored_path, image_bytes
                )

            sha256_hash = hashlib.sha256(image_bytes).hexdigest()
            file_size = len(image_bytes)

            record = ClaimImage(
                claim_id=claim.id,
                original_filename=original_filename,
                content_type=content_type,
                file_path=stored_path,
                file_size_bytes=file_size,
                sha256_hash=sha256_hash,
                is_masked=mask_images,
            )
            db.add(record)
            stored_images.append(record)

            if use_supabase:
                SupabaseMetadataService.insert_claim_image_metadata(
                    claim_reference_id=claim.claim_reference_id,
                    image_path=stored_path,
                    image_hash=sha256_hash,
                )

        if stored_images:
            await db.flush()

        return stored_images

    @staticmethod
    def _write_file(path: str, data: bytes) -> None:
        with open(path, "wb") as handle:
            handle.write(data)

    @staticmethod
    def _infer_extension(content_type: str, filename: str | None) -> str:
        if filename and "." in filename:
            return "." + filename.rsplit(".", 1)[1].lower()

        mapping = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/tiff": ".tiff",
            "image/bmp": ".bmp",
        }
        return mapping.get(content_type, ".bin")

    @staticmethod
    def _build_object_path(
        claim_reference_id: str,
        user_id: int,
        filename: str,
    ) -> str:
        return f"insurer_{user_id}/{claim_reference_id}/{filename}"

    @staticmethod
    async def _upload_to_supabase(
        object_path: str,
        image_bytes: bytes,
        content_type: str,
    ) -> None:
        supabase = get_supabase_client()
        if not supabase:
            return

        file_options = {
            "content-type": content_type,
            "upsert": False,
        }

        await asyncio.to_thread(
            supabase.storage.from_(settings.supabase_storage_bucket).upload,
            object_path,
            image_bytes,
            file_options,
        )

    @staticmethod
    def create_signed_url(object_path: str, expires_in: Optional[int] = None) -> Optional[str]:
        if not is_supabase_configured():
            return None

        supabase = get_supabase_client()
        ttl = expires_in or settings.supabase_signed_url_ttl_seconds
        try:
            response = supabase.storage.from_(settings.supabase_storage_bucket).create_signed_url(
                object_path, ttl
            )
        except Exception:
            return None

        if isinstance(response, dict):
            return response.get("signedURL") or response.get("signed_url")

        signed_url = getattr(response, "signedURL", None) or getattr(response, "signed_url", None)
        if signed_url:
            return signed_url

        data = getattr(response, "data", None)
        if isinstance(data, dict):
            return data.get("signedURL") or data.get("signed_url")

        return None
