from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc, asc
from typing import List, Optional, Dict, Any
from src.models.task import Task, TaskDependency, TaskStatus, TaskPriority
from src.schemas.task import TaskCreate, TaskUpdate
from datetime import datetime


class TaskCRUD:
    @staticmethod
    def get_task(db: Session, task_id: int) -> Optional[Task]:
        return db.query(Task).filter(Task.id == task_id).first()

    @staticmethod
    def get_task_with_dependencies(db: Session, task_id: int) -> Optional[Task]:
        return db.query(Task).options(
            joinedload(Task.dependencies).joinedload(TaskDependency.depends_on_task),
            joinedload(Task.dependent_tasks).joinedload(TaskDependency.task)
        ).filter(Task.id == task_id).first()

    @staticmethod
    def get_tasks(
            db: Session,
            skip: int = 0,
            limit: int = 100,
            filters: Optional[Dict[str, Any]] = None,
            sort_by: Optional[str] = None,
            sort_order: str = "asc"
    ) -> List[Task]:
        query = db.query(Task)

        # Apply filters
        if filters:
            if status := filters.get("status"):
                query = query.filter(Task.status == status)
            if priority := filters.get("priority"):
                query = query.filter(Task.priority == priority)
            if tags := filters.get("tags"):
                # Filter by any of the provided tags
                conditions = []
                for tag in tags:
                    conditions.append(Task.tags.contains([tag]))
                query = query.filter(or_(*conditions))
            if search := filters.get("search"):
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Task.title.ilike(search_term),
                        Task.description.ilike(search_term)
                    )
                )
            if user_id := filters.get("user_id"):
                query = query.filter(Task.user_id == user_id)

        # Apply sorting
        if sort_by:
            sort_column = getattr(Task, sort_by, Task.created_at)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(Task.created_at))

        # Apply pagination
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_tasks_count(db: Session, filters: Optional[Dict[str, Any]] = None) -> int:
        query = db.query(Task)

        if filters:
            if status := filters.get("status"):
                query = query.filter(Task.status == status)
            if priority := filters.get("priority"):
                query = query.filter(Task.priority == priority)
            if tags := filters.get("tags"):
                conditions = []
                for tag in tags:
                    conditions.append(Task.tags.contains([tag]))
                query = query.filter(or_(*conditions))
            if search := filters.get("search"):
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Task.title.ilike(search_term),
                        Task.description.ilike(search_term)
                    )
                )
            if user_id := filters.get("user_id"):
                query = query.filter(Task.user_id == user_id)

        return query.count()

    @staticmethod
    def create_task(db: Session, task_data: TaskCreate, user_id: Optional[int] = None) -> Task:
        # Create task
        db_task = Task(
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            priority=task_data.priority,
            tags=task_data.tags,
            user_id=user_id
        )
        db.add(db_task)
        db.flush()  # Get the task ID

        # Create dependencies
        if task_data.depends_on:
            for depends_on_id in task_data.depends_on:
                if depends_on_id != db_task.id:  # Prevent self-dependency
                    dependency = TaskDependency(
                        task_id=db_task.id,
                        depends_on_id=depends_on_id
                    )
                    db.add(dependency)

        db.commit()
        db.refresh(db_task)
        return db_task

    @staticmethod
    def update_task(db: Session, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        db_task = TaskCRUD.get_task(db, task_id)
        if not db_task:
            return None

        update_data = task_data.dict(exclude_unset=True)

        # Prevent marking task as completed if dependencies aren't done
        if update_data.get("status") == TaskStatus.COMPLETED:
            # Check if all dependencies are completed
            for dependency in db_task.dependencies:
                if dependency.depends_on_task.status != TaskStatus.COMPLETED:
                    raise ValueError(
                        f"Cannot mark task as completed. "
                        f"Dependency task {dependency.depends_on_id} is not completed."
                    )

        for field, value in update_data.items():
            setattr(db_task, field, value)

        db_task.updated_at = datetime.now()
        db.commit()
        db.refresh(db_task)
        return db_task

    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        db_task = TaskCRUD.get_task(db, task_id)
        if not db_task:
            return False

        db.delete(db_task)
        db.commit()
        return True

    @staticmethod
    def add_dependency(db: Session, task_id: int, depends_on_id: int) -> Optional[TaskDependency]:
        # Check if both tasks exist
        task = TaskCRUD.get_task(db, task_id)
        depends_on_task = TaskCRUD.get_task(db, depends_on_id)

        if not task or not depends_on_task:
            return None

        # Check for circular dependency
        if TaskCRUD._has_circular_dependency(db, task_id, depends_on_id):
            raise ValueError("Circular dependency detected")

        # Check if dependency already exists
        existing = db.query(TaskDependency).filter(
            TaskDependency.task_id == task_id,
            TaskDependency.depends_on_id == depends_on_id
        ).first()

        if existing:
            return existing

        dependency = TaskDependency(
            task_id=task_id,
            depends_on_id=depends_on_id
        )
        db.add(dependency)
        db.commit()
        db.refresh(dependency)
        return dependency

    @staticmethod
    def remove_dependency(db: Session, task_id: int, depends_on_id: int) -> bool:
        dependency = db.query(TaskDependency).filter(
            TaskDependency.task_id == task_id,
            TaskDependency.depends_on_id == depends_on_id
        ).first()

        if not dependency:
            return False

        db.delete(dependency)
        db.commit()
        return True

    @staticmethod
    def get_dependency_tree(db: Session, task_id: int) -> Dict[str, Any]:
        """Get the complete dependency tree for a task"""
        task = TaskCRUD.get_task_with_dependencies(db, task_id)
        if not task:
            return {}

        return {
            "task": task,
            "dependencies": [
                TaskCRUD.get_dependency_tree(db, dep.depends_on_id)
                for dep in task.dependencies
            ]
        }

    @staticmethod
    def _has_circular_dependency(db: Session, task_id: int, depends_on_id: int) -> bool:
        """Check if adding a dependency would create a circular reference"""
        # If depends_on_id depends on task_id (directly or indirectly), it's circular
        return TaskCRUD._is_dependent(db, depends_on_id, task_id)

    @staticmethod
    def _is_dependent(db: Session, task_id: int, depends_on_id: int) -> bool:
        """Check if task_id depends on depends_on_id (directly or indirectly)"""
        # Direct dependency
        direct = db.query(TaskDependency).filter(
            TaskDependency.task_id == task_id,
            TaskDependency.depends_on_id == depends_on_id
        ).first()

        if direct:
            return True

        # Indirect dependency - recursively check dependencies of task_id
        dependencies = db.query(TaskDependency).filter(
            TaskDependency.task_id == task_id
        ).all()

        for dep in dependencies:
            if TaskCRUD._is_dependent(db, dep.depends_on_id, depends_on_id):
                return True

        return False


task_crud = TaskCRUD()