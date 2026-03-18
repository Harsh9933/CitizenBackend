from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.models.models import User, Priority
from app.schemas.schemas import (
    ComplaintResponse,
    ComplaintUpdate,
)
from app.auth.auth_utils import get_current_user, require_admin
from app.processing_service.service import ProcessingService
from app.storage.gcs_service import upload_image_to_gcs

router = APIRouter(prefix="/complaints", tags=["Processing Service"])


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint(
    title: str = Form(..., min_length=1, max_length=255),
    description: str = Form(..., min_length=1),
    latitude: float = Form(..., ge=-90, le=90),
    longitude: float = Form(..., ge=-180, le=180),
    priority: Priority = Form(Priority.MEDIUM),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new complaint. Any authenticated user can create.

    Accepts multipart form data. If an image file is provided,
    it will be uploaded to Google Cloud Storage automatically.
    """
    # Upload image to GCS if provided
    image_url = None
    if image and image.filename:
        image_url = await upload_image_to_gcs(image, current_user.id)

    service = ProcessingService(db)
    complaint = await service.create_complaint(
        user_id=current_user.id,
        title=title,
        description=description,
        latitude=latitude,
        longitude=longitude,
        image_url=image_url,
        priority=priority.value,
    )
    return complaint


@router.patch("/{complaint_id}/status", response_model=ComplaintResponse)
async def update_complaint_status(
    complaint_id: int,
    update_data: ComplaintUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update complaint status and/or priority. Admin only."""
    service = ProcessingService(db)
    complaint = await service.update_complaint_status(complaint_id, current_user, update_data)

    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found or insufficient permissions"
        )

    return complaint


@router.patch("/{complaint_id}/resolve", response_model=ComplaintResponse)
async def mark_complaint_resolved(
    complaint_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Mark a complaint as resolved. Admin only."""
    service = ProcessingService(db)
    complaint = await service.mark_resolved(complaint_id, current_user)

    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found"
        )

    return complaint


@router.patch("/{complaint_id}/image", response_model=ComplaintResponse)
async def upload_complaint_image(
    complaint_id: int,
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an image file for a complaint. Only the complaint owner can update.

    The image is uploaded to Google Cloud Storage and the URL is stored.
    """
    # Upload to GCS
    image_url = await upload_image_to_gcs(image, current_user.id)

    service = ProcessingService(db)
    complaint = await service.upload_image_url(
        complaint_id,
        current_user.id,
        image_url,
    )

    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found or you don't have permission to update"
        )

    return complaint


@router.delete("/{complaint_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_complaint(
    complaint_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete a complaint. Admin only."""
    service = ProcessingService(db)
    success = await service.delete_complaint(complaint_id, current_user)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found"
        )

    return None