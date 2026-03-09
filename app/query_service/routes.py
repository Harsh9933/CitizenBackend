from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.config import get_settings
from app.models.models import ComplaintStatus, Priority, User
from app.schemas.schemas import ComplaintResponse, ComplaintListResponse
from app.auth.auth_utils import get_current_user, require_admin
from app.query_service.service import QueryService

router = APIRouter(prefix="/complaints", tags=["Query Service"])
settings = get_settings()


@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a single complaint by ID."""
    service = QueryService(db)
    complaint = await service.get_complaint_by_id(complaint_id)

    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found"
        )

    return complaint


@router.get("/user/me", response_model=ComplaintListResponse)
async def get_my_complaints(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
    status: Optional[ComplaintStatus] = None,
    priority: Optional[Priority] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all complaints for the current authenticated user."""
    service = QueryService(db)
    return await service.get_complaints_by_user(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
        priority=priority
    )


@router.get("/user/{user_id}", response_model=ComplaintListResponse)
async def get_user_complaints(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
    status: Optional[ComplaintStatus] = None,
    priority: Optional[Priority] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all complaints for a specific user. Admin only."""
    service = QueryService(db)
    return await service.get_complaints_by_user(
        user_id=user_id,
        page=page,
        page_size=page_size,
        status=status,
        priority=priority
    )


@router.get("", response_model=ComplaintListResponse)
async def list_all_complaints(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
    status: Optional[ComplaintStatus] = None,
    priority: Optional[Priority] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all complaints with filtering and pagination. Admin only."""
    service = QueryService(db)
    return await service.get_all_complaints(
        page=page,
        page_size=page_size,
        status=status,
        priority=priority
    )