import logging
import uuid
from typing import Optional
from .config import settings


async def upload_file(file_bytes: bytes, filename: str, content_type: str) -> Optional[str]:
    """Upload a file to GCS and return the GCS path."""
    if settings.environment == "development":
        path = f"uploads/{uuid.uuid4()}/{filename}"
        logging.info(f"[GCS mock] Would upload to {path}")
        return path
    try:
        from google.cloud import storage

        client = storage.Client(project=settings.project_id)
        bucket = client.bucket(settings.gcs_bucket)
        gcs_path = f"uploads/{uuid.uuid4()}/{filename}"
        blob = bucket.blob(gcs_path)
        blob.upload_from_string(file_bytes, content_type=content_type)
        return gcs_path
    except Exception as e:
        logging.error(f"GCS upload error: {e}")
        return None


def get_signed_url(gcs_path: str, expiration_seconds: int = 3600) -> Optional[str]:
    """Generate a signed URL for temporary access to a GCS object."""
    if settings.environment == "development":
        return f"http://localhost:9000/{gcs_path}"
    try:
        from google.cloud import storage
        from datetime import timedelta

        client = storage.Client(project=settings.project_id)
        bucket = client.bucket(settings.gcs_bucket)
        blob = bucket.blob(gcs_path)
        return blob.generate_signed_url(expiration=timedelta(seconds=expiration_seconds))
    except Exception as e:
        logging.error(f"GCS signed URL error: {e}")
        return None
