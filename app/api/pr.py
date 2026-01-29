import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.models.pr_bubble import PRStatus
from app.schemas.pr_bubble import (
    PRBubbleActiveListResponse,
    PRBubbleActiveResponse,
    PRBubbleCreate,
    PRBubbleListResponse,
    PRBubbleResponse,
    PRBubbleUpdate,
    PRStatsResponse,
    TrackRequest,
    TrackResponse,
)
from app.services.pr_service import PRService

router = APIRouter(prefix="/api/pr", tags=["PR"])


@router.get("", response_model=PRBubbleListResponse)
async def get_pr_list(
    status: Optional[PRStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    service = PRService(db)
    items, total = await service.get_pr_list(status=status, page=page, limit=limit)
    return PRBubbleListResponse(
        items=[PRBubbleResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/active", response_model=PRBubbleActiveListResponse)
async def get_active_prs(
    limit: Optional[int] = Query(None, ge=1, le=50, description="Max items to return"),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    service = PRService(db)
    items = await service.get_active_prs(limit=limit)
    return PRBubbleActiveListResponse(
        items=[PRBubbleActiveResponse.model_validate(item) for item in items]
    )


@router.get("/{pr_id}", response_model=PRBubbleResponse)
async def get_pr(
    pr_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    service = PRService(db)
    pr = await service.get_pr_by_id(pr_id)
    if not pr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PR not found",
        )
    return PRBubbleResponse.model_validate(pr)


@router.post("", response_model=PRBubbleResponse, status_code=status.HTTP_201_CREATED)
async def create_pr(
    data: PRBubbleCreate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    service = PRService(db)
    pr = await service.create_pr(data)
    return PRBubbleResponse.model_validate(pr)


@router.put("/{pr_id}", response_model=PRBubbleResponse)
async def update_pr(
    pr_id: uuid.UUID,
    data: PRBubbleUpdate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    service = PRService(db)
    pr = await service.update_pr(pr_id, data)
    if not pr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PR not found",
        )
    return PRBubbleResponse.model_validate(pr)


@router.delete("/{pr_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pr(
    pr_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    service = PRService(db)
    deleted = await service.delete_pr(pr_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PR not found",
        )


@router.post("/{pr_id}/duplicate", response_model=PRBubbleResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_pr(
    pr_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    service = PRService(db)
    pr = await service.duplicate_pr(pr_id)
    if not pr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PR not found",
        )
    return PRBubbleResponse.model_validate(pr)


@router.get("/{pr_id}/stats", response_model=PRStatsResponse)
async def get_pr_stats(
    pr_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    service = PRService(db)
    stats = await service.get_pr_stats(pr_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PR not found",
        )
    return PRStatsResponse(**stats)


@router.post("/{pr_id}/track", response_model=TrackResponse)
async def track_pr(
    pr_id: uuid.UUID,
    data: TrackRequest,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    service = PRService(db)
    success = await service.track_pr(pr_id, data.type)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PR not found",
        )
    return TrackResponse(success=True)
