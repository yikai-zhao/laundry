"""
Storage abstraction layer.

- In dev: saves files to local filesystem under STORAGE_ROOT
- In production (when AWS_S3_BUCKET is set): uploads to S3
  Photos are still served via a /storage proxy in dev, but via CloudFront/S3 URL in prod.
"""
import logging
import os
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)

_s3_client = None


def _get_s3():
    global _s3_client
    if _s3_client is None:
        import boto3
        _s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )
    return _s3_client


def save_photo(content: bytes, ext: str) -> tuple[str, str]:
    """
    Save photo content. Returns (file_path_for_db, public_url_for_client).
    file_path_for_db is always "/storage/photos/{uuid}{ext}".
    public_url_for_client is the full URL to serve the file (S3/CloudFront or relative).
    """
    filename = f"{uuid.uuid4()}{ext}"
    rel_path = f"/storage/photos/{filename}"

    if settings.AWS_S3_BUCKET:
        s3_key = f"photos/{filename}"
        s3 = _get_s3()
        s3.put_object(
            Bucket=settings.AWS_S3_BUCKET,
            Key=s3_key,
            Body=content,
            ContentType=_mime_for_ext(ext),
        )
        # If CloudFront domain configured, serve via CDN; otherwise direct S3 URL
        if settings.AWS_CLOUDFRONT_URL:
            public_url = f"{settings.AWS_CLOUDFRONT_URL.rstrip('/')}/{s3_key}"
        else:
            public_url = f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
        return rel_path, public_url
    else:
        # Local filesystem fallback
        photo_dir = os.path.join(settings.STORAGE_ROOT, "photos")
        os.makedirs(photo_dir, exist_ok=True)
        with open(os.path.join(photo_dir, filename), "wb") as f:
            f.write(content)
        return rel_path, rel_path  # relative path, served via FastAPI StaticFiles


def delete_photo(file_path: str):
    """Delete a photo by its stored file_path."""
    filename = os.path.basename(file_path)

    if settings.AWS_S3_BUCKET:
        try:
            _get_s3().delete_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=f"photos/{filename}",
            )
        except Exception as e:
            logger.error("S3 delete failed for %s: %s", filename, e)
    else:
        local_path = os.path.join(settings.STORAGE_ROOT, "photos", filename)
        try:
            if os.path.exists(local_path):
                os.remove(local_path)
        except OSError:
            pass


def get_photo_bytes(file_path: str) -> bytes | None:
    """Read raw photo bytes — used by AI inspection."""
    filename = os.path.basename(file_path)

    if settings.AWS_S3_BUCKET:
        try:
            response = _get_s3().get_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=f"photos/{filename}",
            )
            return response["Body"].read()
        except Exception as e:
            logger.error("S3 read failed for %s: %s", filename, e)
            return None
    else:
        local_path = os.path.join(settings.STORAGE_ROOT, "photos", filename)
        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                return f.read()
        return None


def _mime_for_ext(ext: str) -> str:
    return {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
        ".gif": "image/gif", ".bmp": "image/bmp",
    }.get(ext.lower(), "image/jpeg")
