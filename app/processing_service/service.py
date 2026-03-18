from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.models import Complaint, ComplaintStatus, Priority, User, UserRole
from app.schemas.schemas import ComplaintUpdate


class ProcessingService:
    """Service for handling write operations on complaints."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_complaint(
        self,
        user_id: int,
        title: str,
        description: str,
        latitude: float,
        longitude: float,
        image_url: Optional[str] = None,
        priority: str = Priority.MEDIUM.value,
    ) -> Complaint:
        """Create a new complaint."""
        complaint = Complaint(
            user_id=user_id,
            title=title,
            description=description,
            latitude=latitude,
            longitude=longitude,
            image_url=image_url,
            priority=priority,
            status=ComplaintStatus.PENDING.value,
        )
        self.db.add(complaint)
        await self.db.flush()
        await self.db.refresh(complaint)
        return complaint

    async def update_complaint_status(
        self,
        complaint_id: int,
        user: User,
        update_data: ComplaintUpdate
    ) -> Optional[Complaint]:
        """Update complaint status. Admin only."""
        if user.role != UserRole.ADMIN:
            return None

        result = await self.db.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )
        complaint = result.scalar_one_or_none()

        if not complaint:
            return None

        if update_data.status is not None:
            complaint.status = update_data.status.value if isinstance(update_data.status, ComplaintStatus) else update_data.status
        if update_data.priority is not None:
            complaint.priority = update_data.priority.value if isinstance(update_data.priority, Priority) else update_data.priority

        await self.db.flush()
        await self.db.refresh(complaint)
        return complaint

    async def mark_resolved(self, complaint_id: int, user: User) -> Optional[Complaint]:
        """Mark a complaint as resolved. Admin only."""
        if user.role != UserRole.ADMIN:
            return None

        result = await self.db.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )
        complaint = result.scalar_one_or_none()

        if not complaint:
            return None

        complaint.status = ComplaintStatus.RESOLVED.value
        await self.db.flush()
        await self.db.refresh(complaint)
        return complaint

    async def upload_image_url(
        self,
        complaint_id: int,
        user_id: int,
        image_url: str
    ) -> Optional[Complaint]:
        """Upload image URL to a complaint. User can only update their own complaints."""
        from app.storage.gcs_service import delete_image_from_gcs

        result = await self.db.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )
        complaint = result.scalar_one_or_none()

        if not complaint:
            return None

        # Only complaint owner or admin can update image
        if complaint.user_id != user_id:
            return None

        # Delete the old image from GCS if it exists
        if complaint.image_url:
            await delete_image_from_gcs(complaint.image_url)

        complaint.image_url = image_url
        await self.db.flush()
        await self.db.refresh(complaint)
        return complaint

    async def delete_complaint(self, complaint_id: int, user: User) -> bool:
        """Delete a complaint. Admin only."""
        if user.role != UserRole.ADMIN:
            return False

        result = await self.db.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )
        complaint = result.scalar_one_or_none()

        if not complaint:
            return False

        await self.db.delete(complaint)
        await self.db.flush()
        return True