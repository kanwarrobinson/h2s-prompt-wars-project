from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Project(BaseModel):
    id: Optional[str] = None
    workspace_id: str
    name: str
    description: Optional[str] = None
    color: str = "#6366f1"
    github_repo: Optional[str] = None
    active: bool = True
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    color: str = "#6366f1"
    github_repo: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    color: Optional[str] = None
    github_repo: Optional[str] = None
    active: Optional[bool] = None


class ProjectResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: Optional[str] = None
    color: str
    github_repo: Optional[str] = None
    active: bool
    created_by: Optional[str] = None
    sprint_count: Optional[int] = 0
    task_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime
