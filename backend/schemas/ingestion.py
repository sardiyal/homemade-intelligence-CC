"""Pydantic schemas for ingestion endpoints."""

from pydantic import BaseModel, Field


class InjectTextRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=10)
    url: str = Field("", description="Optional source URL")
    source_id: int | None = None


class InjectUrlRequest(BaseModel):
    url: str = Field(..., description="URL to fetch and extract")
    source_id: int | None = None


class InjectResponse(BaseModel):
    success: bool
    message: str
    content_id: int | None = None


class SourceStatus(BaseModel):
    id: int
    name: str
    feed_url: str | None
    source_type: str | None
    layer: int | None
    bias_label: str | None
    language: str | None
    is_active: bool | None
    article_count: int = 0
    # Extended metadata — bias and framework dimensions
    economic_school: str | None = None
    economic_bias: str | None = None
    analytical_framework: str | None = None
    salience_domains: str | None = None

    model_config = {"from_attributes": True}
