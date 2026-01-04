import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.models.task import Task, TaskStatus, TaskPriority


def test_create_task(client: TestClient):
    """Test creating a task."""
    response = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Test Task",
            "description": "Test Description",
            "status": "pending",
            "priority": "high",
            "tags": ["test", "backend"]
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["status"] == "pending"
    assert data["priority"] == "high"
    assert "test" in data["tags"]


def test_get_tasks(client: TestClient):
    """Test getting list of tasks."""
    # Create some tasks first
    for i in range(3):
        client.post(
            "/api/v1/tasks/",
            json={
                "title": f"Task {i}",
                "description": f"Description {i}",
                "status": "pending",
                "priority": "medium"
            }
        )

    response = client.get("/api/v1/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 3
    assert data["total"] == 3


def test_get_task(client: TestClient):
    """Test getting a single task."""
    # Create a task
    create_response = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Single Task",
            "description": "Single Description"
        }
    )
    task_id = create_response.json()["id"]

    # Get the task
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Single Task"


def test_update_task(client: TestClient):
    """Test updating a task."""
    # Create a task
    create_response = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Update Task",
            "description": "Before Update"
        }
    )
    task_id = create_response.json()["id"]

    # Update the task
    response = client.put(
        f"/api/v1/tasks/{task_id}",
        json={
            "title": "Updated Task",
            "description": "After Update",
            "status": "in_progress"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Task"
    assert data["description"] == "After Update"
    assert data["status"] == "in_progress"


def test_delete_task(client: TestClient):
    """Test deleting a task."""
    # Create a task
    create_response = client.post(
        "/api/v1/tasks/",
        json={
            "title": "Delete Task",
            "description": "To be deleted"
        }
    )
    task_id = create_response.json()["id"]

    # Delete the task
    response = client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/api/v1/tasks/{task_id}")
    assert get_response.status_code == 404


def test_filter_tasks(client: TestClient):
    """Test filtering tasks."""
    # Create tasks with different statuses
    tasks = [
        {"title": "Task 1", "status": "pending", "priority": "high"},
        {"title": "Task 2", "status": "in_progress", "priority": "medium"},
        {"title": "Task 3", "status": "completed", "priority": "low"},
    ]

    for task in tasks:
        client.post("/api/v1/tasks/", json=task)

    # Filter by status
    response = client.get("/api/v1/tasks/?status=pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["status"] == "pending"

    # Filter by priority
    response = client.get("/api/v1/tasks/?priority=high")
    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["priority"] == "high"


def test_task_dependencies(client: TestClient):
    """Test task dependencies."""
    # Create two tasks
    task1_response = client.post(
        "/api/v1/tasks/",
        json={"title": "Task 1"}
    )
    task1_id = task1_response.json()["id"]

    task2_response = client.post(
        "/api/v1/tasks/",
        json={"title": "Task 2"}
    )
    task2_id = task2_response.json()["id"]

    # Add dependency
    response = client.post(
        f"/api/v1/tasks/{task2_id}/dependencies",
        json={"depends_on_id": task1_id}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task2_id
    assert data["depends_on_id"] == task1_id

    # Try to complete task 2 while task 1 is pending (should fail)
    response = client.put(
        f"/api/v1/tasks/{task2_id}",
        json={"status": "completed"}
    )
    assert response.status_code == 400
    assert "Cannot mark task as completed" in response.json()["detail"]