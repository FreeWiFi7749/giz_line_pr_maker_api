import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.pr_bubble import PRStatus, TagType


class PRBubbleBase(BaseModel):
    title: str = Field(..., max_length=60, description="PR title (max 60 characters)")
    description: str = Field(..., max_length=200, description="PR description (max 200 characters)")
    image_url: str = Field(..., max_length=500, description="Image URL")
    link_url: str = Field(..., max_length=500, description="Link URL")
    tag_type: TagType = Field(default=TagType.GIZMART, description="Tag type")
    tag_text: str = Field(default="GIZMART", max_length=50, description="Tag text")
    tag_color: str = Field(default="#FF1BE8", max_length=7, description="Tag color (HEX)")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    priority: Optional[int] = Field(default=None, description="Priority (1 is highest)")
    utm_campaign: Optional[str] = Field(default=None, max_length=100, description="UTM campaign name")

    @field_validator("tag_color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        if not v.startswith("#") or len(v) != 7:
            raise ValueError("Tag color must be a valid HEX color (e.g., #FF1BE8)")
        try:
            int(v[1:], 16)
        except ValueError:
            raise ValueError("Tag color must be a valid HEX color")
        return v.upper()

    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: datetime, info) -> datetime:
        start_date = info.data.get("start_date")
        if start_date and v <= start_date:
            raise ValueError("End date must be after start date")
        return v


class PRBubbleCreate(PRBubbleBase):
    status: PRStatus = Field(default=PRStatus.DRAFT, description="PR status")


class PRBubbleUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=60)
    description: Optional[str] = Field(default=None, max_length=200)
    image_url: Optional[str] = Field(default=None, max_length=500)
    link_url: Optional[str] = Field(default=None, max_length=500)
    tag_type: Optional[TagType] = None
    tag_text: Optional[str] = Field(default=None, max_length=50)
    tag_color: Optional[str] = Field(default=None, max_length=7)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    priority: Optional[int] = None
    status: Optional[PRStatus] = None
    utm_campaign: Optional[str] = Field(default=None, max_length=100)

    @field_validator("tag_color")
    @classmethod
    def validate_hex_color(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not v.startswith("#") or len(v) != 7:
            raise ValueError("Tag color must be a valid HEX color (e.g., #FF1BE8)")
        try:
            int(v[1:], 16)
        except ValueError:
            raise ValueError("Tag color must be a valid HEX color")
        return v.upper()


class PRBubbleResponse(PRBubbleBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: PRStatus
    view_count: int
    click_count: int
    created_at: datetime
    updated_at: datetime


class PRBubbleListResponse(BaseModel):
    items: list[PRBubbleResponse]
    total: int
    page: int
    limit: int


class PRBubbleActiveResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    image_url: str
    link_url: str
    tag_type: TagType
    tag_text: str
    tag_color: str
    priority: Optional[int]
    utm_campaign: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class PRBubbleActiveListResponse(BaseModel):
    items: list[PRBubbleActiveResponse]


class TrackRequest(BaseModel):
    type: str = Field(..., pattern="^(view|click)$", description="Track type: view or click")


class TrackResponse(BaseModel):
    success: bool


class ImageUploadResponse(BaseModel):
    url: str


class PRStatsResponse(BaseModel):
    id: uuid.UUID
    title: str
    view_count: int
    click_count: int
    ctr: float = Field(description="Click-through rate")
    created_at: datetime
    start_date: datetime
    end_date: datetime
    status: PRStatus
