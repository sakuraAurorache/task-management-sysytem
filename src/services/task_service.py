from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from src.crud.task import task_crud
from src.crud.cache import CacheManager
from src.schemas.task import TaskCreate, TaskUpdate, TaskInDB, TaskListResponse
from redis import Redis
import hashlib


class TaskService:
    def __init__(self, db: Session, cache_manager: CacheManager):
        self.db = db
        self.cache = cache_manager

    def get_task(self, task_id: int) -> Optional[TaskInDB]:
        # Try cache first
        cache_key = f"task:{task_id}"
        cached_task = self.cache.get(cache_key)
        if cached_task:
            return TaskInDB(**cached_task)

        # Get from database
        task = task_crud.get_task(self.db, task_id)
        if task:
            task_dict = TaskInDB.from_orm(task).dict()
            self.cache.set(cache_key, task_dict)
            return TaskInDB(**task_dict)

        return None

    def get_tasks(
            self,
            skip: int = 0,
            limit: int = 100,
            filters: Optional[Dict[str, Any]] = None,
            sort_by: Optional[str] = None,
            sort_order: str = "asc"
    ) -> TaskListResponse:
        # Create cache key based on query parameters
        cache_params = {
            "skip": skip,
            "limit": limit,
            "filters": filters or {},
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        param_hash = hashlib.md5(str(cache_params).encode()).hexdigest()
        cache_key = f"tasks:{param_hash}"

        # Try cache first
        cached = self.cache.get(cache_key)
        if cached:
            return TaskListResponse(**cached)

        # Get from database
        tasks = task_crud.get_tasks(
            self.db, skip, limit, filters, sort_by, sort_order
        )
        total = task_crud.get_tasks_count(self.db, filters)

        response = TaskListResponse(
            tasks=[TaskInDB.from_orm(task) for task in tasks],
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            page_size=limit,
            total_pages=(total + limit - 1) // limit if limit > 0 else 1
        )

        # Cache the result
        self.cache.set(cache_key, response.dict())
        return response

    def create_task(self, task_data: TaskCreate, user_id: Optional[int] = None) -> TaskInDB:
        task = task_crud.create_task(self.db, task_data, user_id)

        # Clear task list cache
        self.cache.clear_task_cache()

        return TaskInDB.from_orm(task)

    def update_task(self, task_id: int, task_data: TaskUpdate) -> Optional[TaskInDB]:
        task = task_crud.update_task(self.db, task_id, task_data)
        if task:
            # Clear cache for this task and task lists
            self.cache.clear_task_cache(task_id)
            return TaskInDB.from_orm(task)
        return None

    def delete_task(self, task_id: int) -> bool:
        result = task_crud.delete_task(self.db, task_id)
        if result:
            # Clear cache
            self.cache.clear_task_cache(task_id)
        return result

    def get_dependency_tree(self, task_id: int) -> Dict[str, Any]:
        cache_key = f"task_dependencies:{task_id}"

        # Try cache first
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        tree = task_crud.get_dependency_tree(self.db, task_id)

        # Cache the result
        self.cache.set(cache_key, tree)
        return tree

    def add_dependency(self, task_id: int, depends_on_id: int) -> Optional[Dict[str, Any]]:
        dependency = task_crud.add_dependency(self.db, task_id, depends_on_id)
        if dependency:
            # Clear cache for both tasks
            self.cache.clear_task_cache(task_id)
            self.cache.clear_task_cache(depends_on_id)
            return {
                "id": dependency.id,
                "task_id": dependency.task_id,
                "depends_on_id": dependency.depends_on_id,
                "created_at": dependency.created_at
            }
        return None

    def remove_dependency(self, task_id: int, depends_on_id: int) -> bool:
        result = task_crud.remove_dependency(self.db, task_id, depends_on_id)
        if result:
            # Clear cache for both tasks
            self.cache.clear_task_cache(task_id)
            self.cache.clear_task_cache(depends_on_id)
        return result