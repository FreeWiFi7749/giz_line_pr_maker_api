import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pr_bubble import PRBubble, PRStatus
from app.schemas.pr_bubble import PRBubbleCreate, PRBubbleUpdate


class PRService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_pr_list(
        self,
        status: Optional[PRStatus] = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[PRBubble], int]:
        query = select(PRBubble)

        if status:
            query = query.where(PRBubble.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(PRBubble.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_pr_by_id(self, pr_id: uuid.UUID) -> Optional[PRBubble]:
        query = select(PRBubble).where(PRBubble.id == pr_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_pr(self, data: PRBubbleCreate) -> PRBubble:
        pr = PRBubble(**data.model_dump())
        self.db.add(pr)
        await self.db.flush()
        await self.db.refresh(pr)
        return pr

    async def update_pr(self, pr_id: uuid.UUID, data: PRBubbleUpdate) -> Optional[PRBubble]:
        pr = await self.get_pr_by_id(pr_id)
        if not pr:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(pr, field, value)

        pr.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(pr)
        return pr

    async def delete_pr(self, pr_id: uuid.UUID) -> bool:
        pr = await self.get_pr_by_id(pr_id)
        if not pr:
            return False

        await self.db.delete(pr)
        await self.db.flush()
        return True

    async def duplicate_pr(self, pr_id: uuid.UUID) -> Optional[PRBubble]:
        original = await self.get_pr_by_id(pr_id)
        if not original:
            return None

        new_title = f"{original.title[:35]}(コピー)" if len(original.title) > 35 else f"{original.title}(コピー)"
        if len(new_title) > 40:
            new_title = new_title[:40]

        new_pr = PRBubble(
            title=new_title,
            description=original.description,
            image_url=original.image_url,
            link_url=original.link_url,
            tag_type=original.tag_type,
            tag_text=original.tag_text,
            tag_color=original.tag_color,
            start_date=original.start_date,
            end_date=original.end_date,
            priority=original.priority,
            status=PRStatus.DRAFT,
            utm_campaign=original.utm_campaign,
            view_count=0,
            click_count=0,
        )

        self.db.add(new_pr)
        await self.db.flush()
        await self.db.refresh(new_pr)
        return new_pr

    async def get_active_prs(self, limit: Optional[int] = None) -> list[PRBubble]:
        now = datetime.now(timezone.utc)

        query = (
            select(PRBubble)
            .where(PRBubble.status == PRStatus.ACTIVE)
            .where(PRBubble.start_date <= now)
            .where(PRBubble.end_date >= now)
            .order_by(
                PRBubble.priority.asc().nullslast(),
                PRBubble.created_at.desc(),
            )
        )

        if limit:
            query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def track_pr(self, pr_id: uuid.UUID, track_type: str) -> bool:
        pr = await self.get_pr_by_id(pr_id)
        if not pr:
            return False

        if track_type == "view":
            pr.view_count += 1
        elif track_type == "click":
            pr.click_count += 1
        else:
            return False

        await self.db.flush()
        return True

    async def get_pr_stats(self, pr_id: uuid.UUID) -> Optional[dict]:
        pr = await self.get_pr_by_id(pr_id)
        if not pr:
            return None

        ctr = (pr.click_count / pr.view_count * 100) if pr.view_count > 0 else 0.0

        return {
            "id": pr.id,
            "title": pr.title,
            "view_count": pr.view_count,
            "click_count": pr.click_count,
            "ctr": round(ctr, 2),
            "created_at": pr.created_at,
            "start_date": pr.start_date,
            "end_date": pr.end_date,
            "status": pr.status,
        }
