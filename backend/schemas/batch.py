"""Pydantic schemas for batch report generation."""

from pydantic import BaseModel, Field


class BatchGenerateRequest(BaseModel):
    days_lookback: int = Field(7, ge=1, le=30, description="Days of recent content to scan for topics")
    max_topics: int = Field(10, ge=1, le=20, description="Number of topics to identify and generate")


class IdentifiedTopic(BaseModel):
    topic: str = Field(..., description="Analysis topic string (5-100 words)")
    domain: str = Field(..., description="geopolitics / markets / taiwan / energy / general")
    rationale: str = Field(..., description="Why this topic is important right now")
