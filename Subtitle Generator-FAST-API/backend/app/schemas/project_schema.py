from pydantic import BaseModel, Field


class ProjectSummary(BaseModel):
    id: str
    original_filename: str
    language: str | None = None
    status: str
    progress: int = 0
    error: str | None = None
    has_srt: bool = False
    created_at: str | None = None
    updated_at: str | None = None


class ProjectCreateResponse(BaseModel):
    id: str
    status: str


class PresignedUrlResponse(BaseModel):
    url: str = Field(..., description="Time-limited S3 GET URL")
