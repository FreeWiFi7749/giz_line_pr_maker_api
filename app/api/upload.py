from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.auth import verify_cf_access
from app.schemas.pr_bubble import ImageUploadResponse
from app.services.r2_service import R2Service, get_r2_service

router = APIRouter(prefix="/api/upload", tags=["Upload"])

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}

MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/image", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    r2_service: R2Service = Depends(get_r2_service),
    _: dict = Depends(verify_cf_access),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    try:
        url = await r2_service.upload_image(
            file_content=content,
            filename=file.filename or "image.jpg",
            content_type=file.content_type or "image/jpeg",
        )
        return ImageUploadResponse(url=url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}",
        )
