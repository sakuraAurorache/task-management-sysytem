#!/usr/bin/env python3
"""
Seed sample data for testing.
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models.task import Task, TaskStatus, TaskPriority
from src.models.user import User
from src.utils.security import get_password_hash


def seed_data():
    """Seed sample data."""
    db = SessionLocal()

    try:
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            is_admin=True
        )
        db.add(admin_user)

        # Create regular user
        regular_user = User(
            username="user",
            email="user@example.com",
            hashed_password=get_password_hash("user123")
        )
        db.add(regular_user)

        db.flush()  # Get user IDs

        # Create sample tasks
        tasks = [
            Task(
                title="Complete project proposal",
                description="Write and submit the project proposal document",
                status=TaskStatus.COMPLETED,
                priority=TaskPriority.HIGH,
                tags=["work", "urgent"],
                user_id=admin_user.id
            ),
            Task(
                title="Prepare presentation",
                description="Create slides for the team meeting",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.MEDIUM,
                tags=["meeting", "presentation"],
                user_id=admin_user.id
            ),
            Task(
                title="Review code changes",
                description="Review pull request #123",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                tags=["code-review", "github"],
                user_id=regular_user.id
            ),
            Task(
                title="Update documentation",
                description="Update API documentation with new endpoints",
                status=TaskStatus.PENDING,
                priority=TaskPriority.LOW,
                tags=["docs", "api"],
                user_id=regular_user.id
            ),
            Task(
                title="Team lunch",
                description="Organize team lunch this Friday",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                tags=["team-building", "social"],
                user_id=regular_user.id
            )
        ]

        for task in tasks:
            db.add(task)

        db.flush()  # Get task IDs

        # Create task dependencies
        if len(tasks) >= 2:
            from src.models.task import TaskDependency
            dependency = TaskDependency(
                task_id=tasks[1].id,  # Prepare presentation
                depends_on_id=tasks[0].id  # Complete project proposal
            )
            db.add(dependency)

        db.commit()
        print("Sample data seeded successfully!")

        # Print credentials for testing
        print("\nTest credentials:")
        print("Admin: username=admin, password=admin123")
        print("User: username=user, password=user123")

    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()