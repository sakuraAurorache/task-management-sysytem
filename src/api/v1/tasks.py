from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from src.database import get_db, get_redis
from src.crud.cache import CacheManager
from src.services.task_service import TaskService
from src.schemas.task import (
    TaskCreate, TaskUpdate, TaskInDB, TaskListResponse,
    TaskDependencyCreate, TaskDependencyResponse
)
from src.models.task import TaskStatus, TaskPriority
from redis import Redis

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_service(
        db: Session = Depends(get_db),
        redis: Redis = Depends(get_redis)
) -> TaskService:
    cache_manager = CacheManager(redis)
    return TaskService(db, cache_manager)


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
        skip: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(100, ge=1, le=1000, description="Number of items to return"),
        status: Optional[TaskStatus] = Query(None, description="Filter by status"),
        priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
        tags: Optional[List[str]] = Query(None, description="Filter by tags"),
        search: Optional[str] = Query(None, description="Search in title and description"),
        sort_by: Optional[str] = Query(None, description="Field to sort by"),
        sort_order: str = Query("asc", description="Sort order (asc/desc)"),
        service: TaskService = Depends(get_task_service)
):
    """
    Get list of tasks with filtering, sorting, and pagination.
    """
    filters = {}
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    if tags:
        filters["tags"] = tags
    if search:
        filters["search"] = search

    return service.get_tasks(
        skip=skip,
        limit=limit,
        filters=filters,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get("/{task_id}", response_model=TaskInDB)
async def get_task(
        task_id: int,
        service: TaskService = Depends(get_task_service)
):
    """
    Get a specific task by ID.
    """
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@router.post("/", response_model=TaskInDB, status_code=status.HTTP_201_CREATED)
async def create_task(
        task_data: TaskCreate,
        service: TaskService = Depends(get_task_service)
):
    """
    Create a new task.
    """
    try:
        return service.create_task(task_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{task_id}", response_model=TaskInDB)
async def update_task(
        task_id: int,
        task_data: TaskUpdate,
        service: TaskService = Depends(get_task_service)
):
    """
    Update an existing task.
    """
    task = service.update_task(task_id, task_data)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
        task_id: int,
        service: TaskService = Depends(get_task_service)
):
    """
    Delete a task.
    """
    if not service.delete_task(task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )


@router.get("/{task_id}/dependencies")
async def get_task_dependencies(
        task_id: int,
        service: TaskService = Depends(get_task_service)
):
    """
    Get dependency tree for a task.
    """
    tree = service.get_dependency_tree(task_id)
    if not tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return tree


@router.post("/{task_id}/dependencies", response_model=TaskDependencyResponse)
async def add_dependency(
        task_id: int,
        dependency_data: TaskDependencyCreate,
        service: TaskService = Depends(get_task_service)
):
    """
    Add a dependency to a task.
    """
    dependency = service.add_dependency(task_id, dependency_data.depends_on_id)
    if not dependency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task or dependency not found"
        )
    return dependency


@router.delete("/{task_id}/dependencies/{depends_on_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_dependency(
        task_id: int,
        depends_on_id: int,
        service: TaskService = Depends(get_task_service)
):
    """
    Remove a dependency from a task.
    """
    if not service.remove_dependency(task_id, depends_on_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found"
        )