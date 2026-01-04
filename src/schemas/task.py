from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
from src.models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    tags: Optional[List[str]] = Field(default_factory=list)

    @validator('tags')
    def validate_tags(cls, v):
        if v is not None:
            for tag in v:
                if len(tag) > 50:
                    raise ValueError(f"Tag '{tag}' exceeds maximum length of 50 characters")
        return v


class TaskCreate(TaskBase):
    depends_on: Optional[List[int]] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    tags: Optional[List[str]] = None


class TaskInDB(TaskBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    user_id: Optional[int]

    class Config:
        from_attributes = True


class TaskWithDependencies(TaskInDB):
    dependencies: List["TaskInDB"] = []
    dependent_tasks: List["TaskInDB"] = []


class TaskListResponse(BaseModel):
    tasks: List[TaskInDB]
    total: int
    page: int
    page_size: int
    total_pages: int


class TaskDependencyCreate(BaseModel):
    depends_on_id: int


class TaskDependencyResponse(BaseModel):
    id: int
    task_id: int
    depends_on_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Update forward reference
TaskWithDependencies.update_forward_refs()