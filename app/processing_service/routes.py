from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import (
    ComplaintCreate,
    ComplaintResponse,
    ComplaintUpdate,
    ImageUpload,
)
from app.auth.auth_utils import get_current_user, require_admin
from app.processing_service.service import ProcessingService

router = APIRouter(prefix="/complaints", tags=["Processing Service"])


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
async def create_complaint(
    complaint_data: ComplaintCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new complaint. Any authenticated user can create."""
    service = ProcessingService(db)
    complaint = await service.create_complaint(current_user.id, complaint_data)
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
async def upload_image_url(
    complaint_id: int,
    image_data: ImageUpload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload image URL for a complaint. Only complaint owner can update."""
    service = ProcessingService(db)
    complaint = await service.upload_image_url(
        complaint_id,
        current_user.id,
        image_data.image_url
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