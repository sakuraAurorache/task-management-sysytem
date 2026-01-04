from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, JSON, ForeignKey, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base
import enum


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
        index=True
    )
    priority = Column(
        Enum(TaskPriority),
        default=TaskPriority.MEDIUM,
        nullable=False,
        index=True
    )
    tags = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    dependencies = relationship(
        "TaskDependency",
        primaryjoin="Task.id==TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    dependent_tasks = relationship(
        "TaskDependency",
        primaryjoin="Task.id==TaskDependency.depends_on_id",
        back_populates="depends_on_task"
    )


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    depends_on_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on_task = relationship("Task", foreign_keys=[depends_on_id], back_populates="dependent_tasks")

    __table_args__ = (
        # Ensure a task cannot depend on itself
        CheckConstraint('task_id != depends_on_id', name='no_self_dependency'),
        # Ensure no duplicate dependencies
        CheckConstraint('(task_id, depends_on_id) in (select task_id, depends_on_id from task_dependencies)', name='unique_dependency')
    )