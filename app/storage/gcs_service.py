"""
Google Cloud Storage service for handling image uploads.

This module provides async-compatible file upload to GCS buckets.
The uploaded files are made publicly readable and the public URL is returned.
"""

import uuid
from datetime import datetime
from fastapi import UploadFile, HTTPException, status
from google.cloud import storage
from functools import lru_cache

from app.core.config import get_settings

# Allowed image MIME types
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}

# Max file size: 10 MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Map MIME types to file extensions
MIME_TO_EXTENSION = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


@lru_cache()
def _get_gcs_client() -> storage.Client:
    """Get a cached GCS client instance."""
    settings = get_settings()
    return storage.Client(project=settings.GCS_PROJECT_ID)


def _get_bucket() -> storage.Bucket:
    """Get the configured GCS bucket."""
    settings = get_settings()
    client = _get_gcs_client()
    return client.bucket(settings.GCS_BUCKET_NAME)


def _generate_blob_name(user_id: int, original_filename: str, content_type: str) -> str:
    """
    Generate a unique blob name to avoid collisions.
    Format: complaints/{user_id}/{date}/{uuid}{extension}
    """
    ext = MIME_TO_EXTENSION.get(content_type, ".jpg")
    date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
    unique_id = uuid.uuid4().hex[:12]
    return f"complaints/{user_id}/{date_prefix}/{unique_id}{ext}"


async def upload_image_to_gcs(file: UploadFile, user_id: int) -> str:
    """
    Upload an image file to Google Cloud Storage and return its public URL.

    Args:
        file: The uploaded file from the request.
        user_id: The ID of the user uploading the image.

    Returns:
        The public URL of the uploaded image.

    Raises:
        HTTPException: If the file type is not allowed or the file is too large.
    """
    # --- Validate content type ---
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' is not allowed. "
                   f"Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    # --- Read file contents ---
    contents = await file.read()

    # --- Validate file size ---
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the maximum allowed size of "
                   f"{MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.",
        )

    # --- Upload to GCS ---
    bucket = _get_bucket()
    blob_name = _generate_blob_name(user_id, file.filename or "image", file.content_type)
    blob = bucket.blob(blob_name)

    blob.upload_from_string(
        contents,
        content_type=file.content_type,
    )

    # Construct the public URL directly
    # (public access is managed at the bucket IAM level, not per-object ACL)
    settings = get_settings()
    public_url = f"https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/{blob_name}"

    return public_url


async def delete_image_from_gcs(image_url: str) -> bool:
    """
    Delete an image from GCS given its public URL.

    Args:
        image_url: The public URL of the image to delete.

    Returns:
        True if the image was deleted, False if it was not found.
    """
    settings = get_settings()
    bucket = _get_bucket()

    # Extract blob name from public URL
    # Public URL format: https://storage.googleapis.com/{bucket_name}/{blob_name}
    prefix = f"https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/"
    if not image_url.startswith(prefix):
        return False

    blob_name = image_url[len(prefix):]
    blob = bucket.blob(blob_name)

    if blob.exists():
        blob.delete()
        return True

    return False
