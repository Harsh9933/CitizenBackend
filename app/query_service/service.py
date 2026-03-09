from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from typing import Optional
import math

from app.models.models import Complaint, ComplaintStatus, Priority, User, UserRole
from app.schemas.schemas import ComplaintListResponse, ComplaintResponse


class QueryService:
    """Service for handling read operations on complaints."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_complaint_by_id(self, complaint_id: int) -> Optional[Complaint]:
        """Get a single complaint by ID."""
        result = await self.db.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )
        return result.scalar_one_or_none()

    async def get_complaints_by_user(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        status: Optional[ComplaintStatus] = None,
        priority: Optional[Priority] = None
    ) -> ComplaintListResponse:
        """Get all complaints for a specific user with filtering and pagination."""
        # Build query
        query = select(Complaint).where(Complaint.user_id == user_id)
        count_query = select(func.count()).select_from(Complaint).where(Complaint.user_id == user_id)

        # Apply filters
        filters = []
        if status:
            filters.append(Complaint.status == status)
        if priority:
            filters.append(Complaint.priority == priority)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Complaint.created_at.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        complaints = result.scalars().all()

        pages = math.ceil(total / page_size) if total > 0 else 1

        return ComplaintListResponse(
            items=[ComplaintResponse.model_validate(c) for c in complaints],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )

    async def get_all_complaints(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[ComplaintStatus] = None,
        priority: Optional[Priority] = None
    ) -> ComplaintListResponse:
        """Get all complaints with filtering and pagination. Admin only."""
        # Build query
        query = select(Complaint)
        count_query = select(func.count()).select_from(Complaint)

        # Apply filters
        filters = []
        if status:
            filters.append(Complaint.status == status)
        if priority:
            filters.append(Complaint.priority == priority)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Complaint.created_at.desc()).offset(offset).limit(page_size)

        result = await self.db.execute(query)
        complaints = result.scalars().all()

        pages = math.ceil(total / page_size) if total > 0 else 1

        return ComplaintListResponse(
            items=[ComplaintResponse.model_validate(c) for c in complaints],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages
        )

    async def get_complaints_by_status(
        self,
        status: ComplaintStatus,
        page: int = 1,
        page_size: int = 20
    ) -> ComplaintListResponse:
        """Get complaints filtered by status."""
        return await self.get_all_complaints(page=page, page_size=page_size, status=status)

    async def get_complaints_by_priority(
        self,
        priority: Priority,
        page: int = 1,
        page_size: int = 20
    ) -> ComplaintListResponse:
        """Get complaints filtered by priority."""
        return await self.get_all_complaints(page=page, page_size=page_size, priority=priority)