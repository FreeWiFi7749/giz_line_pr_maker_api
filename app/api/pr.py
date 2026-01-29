import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

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


def is_valid_redirect_url(url: str) -> bool:
    """
    Validate redirect URL to prevent open redirect attacks.
    Only allows http/https schemes.
    """
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        if not parsed.netloc:
            return False
        return True
    except Exception:
        return False


def build_redirect_url_with_utm(base_url: str, utm_campaign: str, utm_content: str) -> str:
    """
    Build redirect URL with UTM parameters using proper URL parsing.
    Handles existing query params (including multi-valued) and fragments correctly.
    """
    parts = urlsplit(base_url)
    utm_keys = {"utm_source", "utm_medium", "utm_campaign", "utm_content"}
    query_pairs = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k not in utm_keys
    ]
    query_pairs += [
        ("utm_source", "line"),
        ("utm_medium", "pr_bubble"),
        ("utm_campaign", utm_campaign),
        ("utm_content", utm_content),
    ]
    new_query = urlencode(query_pairs, doseq=True)
    return urlunsplit(parts._replace(query=new_query))


@router.get("/{pr_id}/redirect")
async def redirect_pr(
    pr_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Redirect endpoint for click tracking.
    Records a click and redirects to the PR's link_url with UTM parameters.
    No API key required as this is accessed directly by users.
    """
    service = PRService(db)
    pr = await service.get_pr_by_id(pr_id)
    if not pr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PR not found",
        )

    if not is_valid_redirect_url(pr.link_url):
        logger.warning(
            "Invalid redirect URL detected: pr_id=%s, url=%s",
            pr_id,
            pr.link_url,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect target",
        )

    await service.track_pr(pr_id, "click")

    utm_campaign = pr.utm_campaign or f"pr_{pr_id}"
    utm_content = datetime.now(timezone.utc).strftime("%Y%m%d_%H%MZ")

    redirect_url = build_redirect_url_with_utm(pr.link_url, utm_campaign, utm_content)
    return RedirectResponse(url=redirect_url, status_code=302)
