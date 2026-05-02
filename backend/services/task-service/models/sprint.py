from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SprintStatus(str, Enum):
    planned = "planned"
    active = "active"
    completed = "completed"


class Sprint(BaseModel):
    id: Optional[str] = None
    workspace_id: str
    project_id: str
    name: str
    goal: Optional[str] = None
    status: SprintStatus = SprintStatus.planned
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    velocity: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SprintCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    goal: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    velocity: Optional[int] = Field(None, ge=0)


class SprintUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    goal: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    velocity: Optional[int] = Field(None, ge=0)


class SprintResponse(BaseModel):
    id: str
    workspace_id: str
    project_id: str
    name: str
    goal: Optional[str] = None
    status: SprintStatus
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    velocity: Optional[int] = None
    task_count: Optional[int] = 0
    completed_task_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime
