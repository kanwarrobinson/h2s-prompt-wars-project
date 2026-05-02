from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    task = "task"
    bug = "bug"
    story = "story"
    epic = "epic"


class TaskStatus(str, Enum):
    backlog = "backlog"
    todo = "todo"
    in_progress = "in_progress"
    review = "review"
    done = "done"


class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TaskComment(BaseModel):
    id: Optional[str] = None
    author_id: str
    content: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TaskAttachment(BaseModel):
    id: Optional[str] = None
    filename: str
    content_type: str
    gcs_path: str
    uploaded_by: str
    uploaded_at: Optional[datetime] = None
    size_bytes: Optional[int] = None


class Task(BaseModel):
    id: Optional[str] = None
    workspace_id: str
    project_id: Optional[str] = None
    sprint_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    type: TaskType = TaskType.task
    status: TaskStatus = TaskStatus.backlog
    priority: TaskPriority = TaskPriority.medium
    assignee_ids: list[str] = []
    reporter_id: str
    labels: list[str] = []
    story_points: Optional[int] = None
    due_date: Optional[datetime] = None
    github_pr_urls: list[str] = []
    comments: list[TaskComment] = []
    attachments: list[TaskAttachment] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"populate_by_name": True}


class TaskCreate(BaseModel):
    workspace_id: str
    project_id: Optional[str] = None
    sprint_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    type: TaskType = TaskType.task
    status: TaskStatus = TaskStatus.backlog
    priority: TaskPriority = TaskPriority.medium
    assignee_ids: list[str] = []
    labels: list[str] = []
    story_points: Optional[int] = Field(None, ge=0, le=100)
    due_date: Optional[datetime] = None
    github_pr_urls: list[str] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    type: Optional[TaskType] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    sprint_id: Optional[str] = None
    project_id: Optional[str] = None
    assignee_ids: Optional[list[str]] = None
    labels: Optional[list[str]] = None
    story_points: Optional[int] = Field(None, ge=0, le=100)
    due_date: Optional[datetime] = None
    github_pr_urls: Optional[list[str]] = None


class TaskResponse(BaseModel):
    id: str
    workspace_id: str
    project_id: Optional[str] = None
    sprint_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    type: TaskType
    status: TaskStatus
    priority: TaskPriority
    assignee_ids: list[str] = []
    reporter_id: str
    labels: list[str] = []
    story_points: Optional[int] = None
    due_date: Optional[datetime] = None
    github_pr_urls: list[str] = []
    comments: list[TaskComment] = []
    attachments: list[TaskAttachment] = []
    created_at: datetime
    updated_at: datetime
