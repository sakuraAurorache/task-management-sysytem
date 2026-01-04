# task-management-sysytem
Role Track:Backend Developer

# Tech Stack

Language: Python 3.12

Framework: FastAPI

Database: MySQL 8.0 + Redis 7

ORM: SQLAlchemy 2.0

Cache: Redis

Containerization: Docker & Docker Compose

Testing: Pytest

Code Formatting: Black

API Documentation: Swagger UI & ReDoc

Authentication: JWT Tokens

# Features Implemented

# Core Features
Complete Task CRUD operations

Data validation and error handling

Database models with migrations (Alembic)

RESTful API design with proper HTTP status codes

# Advanced Backend Features
Task filtering and sorting (status, priority, tags, search)

Pagination support

Task dependency system with circular dependency prevention

Validation to prevent task completion with unfinished dependencies

Task dependency tree queries

# Performance Optimization
Redis caching layer for frequently accessed data

Database connection pooling

Query optimization with proper indexing

API response time < 100ms for basic operations (with cache)

# System Architecture (reference ai )
Scalable multi-tier architecture (Controller-Service-Repository) here v1 -> services - > crud cuz i learned Java Spring Boot before and FastApi study very quick

Docker containerization for all services

Rate limiting middleware

Clear separation of concerns

# Security Features
JWT-based user authentication

Password hashing with bcrypt

CORS configuration

Input validation using Pydantic models

SQL injection prevention through ORM

# Setup Instructions (i dont know too much about docker so here asked AI)
# Prerequisites
Docker and Docker Compose (recommended)

OR Python 3.11+, MySQL 8.0, and Redis 7 installed locally

## Installation Steps (Using Docker )

1. **Clone the repository:**

bash

```
git clone <repository-url>
cd task-manager-backend
```

2. **Configure environment variables:**

bash

```
cp .env.example .env
# Edit .env file with your configuration
```

3. **Start all services with Docker Compose:**

bash

```
docker-compose up -d
```

4. **Run database migrations:**

bash

```
docker-compose exec app alembic upgrade head
```

5. **Seed sample data (optional):**

bash


docker-compose exec app python scripts/seed_data.py

# Configuration
Key environment variables in .env file:

DATABASE_URL: MySQL connection string

REDIS_URL: Redis connection string

SECRET_KEY: JWT secret key

DEBUG: Enable debug mode

RATE_LIMIT_PER_MINUTE: API rate limit

CACHE_TTL: Cache time-to-live in seconds

# API Documentation
Once the application is running, comprehensive API documentation is available at:

Swagger UI: http://localhost:8000/api/docs

ReDoc: http://localhost:8000/api/redoc

### Key Endpoints

#### Authentication

http

```
POST /api/v1/users/
Content-Type: application/json
{
  "username": "testuser",
  "email": "user@example.com",
  "password": "securepassword"
}
```

http

```
POST /api/v1/users/login
Content-Type: application/x-www-form-urlencoded
username: testuser
password: securepassword
```

#### Task Management

**Get tasks with filtering:**

http

```
GET /api/v1/tasks/?status=pending&priority=high&tags=urgent&sort_by=created_at&sort_order=desc&skip=0&limit=10
```

**Create a task:**

http

```
POST /api/v1/tasks/
Content-Type: application/json
{
  "title": "Complete project report",
  "description": "Finish the quarterly project report",
  "status": "pending",
  "priority": "high",
  "tags": ["work", "report", "urgent"],
  "depends_on": [1, 2]
}
```

**Update a task:**

http

```
PUT /api/v1/tasks/{task_id}
Content-Type: application/json
{
  "status": "in_progress",
  "priority": "medium"
}
```

**Add task dependency:**

http

```
POST /api/v1/tasks/{task_id}/dependencies
Content-Type: application/json
{
  "depends_on_id": 3
}
```

#### System Status

http

```
GET /api/status
GET /
```

## Design Decisions

### Why FastAPI?

* ​**Performance**​: Built on Starlette and Pydantic, offering high performance
* ​**Type Safety**​: Native Python type hints with Pydantic validation
* ​**Async Support**​: Native async/await support for I/O bound operations
* ​**Automatic Documentation**​: Built-in OpenAPI and Swagger UI generation
* ​**Modern Features**​: Dependency injection system, background tasks, WebSocket support

### Why MySQL?

* ​**Relational Data**​: Task dependencies are relational in nature
* ​**ACID Compliance**​: Ensures data integrity for task operations
* ​**Mature Ecosystem**​: Widely used with excellent tooling and community support
* ​**Transactions**​: Required for maintaining data consistency in complex operations

### Why Redis?

* ​**Performance**​: In-memory data store for fast caching
* ​**Data Structures**​: Supports strings, lists, sets, hashes, etc.
* ​**Cache Invalidation**​: Built-in TTL support for automatic cache expiration
* ​**Persistence**​: Optional persistence to disk

### Challenge : Cache Invalidation

​**Problem**​: Maintaining cache consistency when task data changes. When a task is updated, all cached data related to that task and task lists need to be invalidated.

​**Solution**​: Implemented a systematic cache invalidation strategy:

1. Clear specific task cache on individual task operations
2. Clear task list cache patterns on any task modification
3. Use cache keys with patterns for batch invalidation
4. Implemented a CacheManager class to centralize cache operations

python

```
def clear_task_cache(self, task_id: Optional[int] = None):
    """Clear task-related cache"""
    if task_id:
        self.delete(f"task:{task_id}")
        self.delete(f"task_dependencies:{task_id}")
    self.delete_pattern("tasks:*")
```

## Future Improvements

### Short-term Improvements (1-2 weeks)

1. **Complete Authentication System**
   * Role-based access control
   * API key authentication for machine-to-machine communication
   * Refresh token mechanism
2. **Enhanced Search**
   * Full-text search with MySQL or Elasticsearch integration
   * Advanced filtering options (date ranges, compound conditions)
   * Saved search queries
3. **WebSocket Support**
   * Real-time task updates
   * Live collaboration features
   * Notification system
4. **File Attachments**
   * Upload and manage task attachments
   * Integration with cloud storage (S3, Google Cloud Storage)
   * File preview and versioning

### Long-term Improvements (3-6 months)

1. **Microservices Architecture**
   * Split into task service, user service, notification service
   * API Gateway for routing and composition
   * Service discovery and configuration management
2. **AI/ML Integration**
   * Intelligent task prioritization
   * Automated task categorization
   * Deadline prediction
   * Workload balancing suggestions
3. **Multi-tenancy Support**
   * Organization/team structure
   * Shared workspaces
   * Cross-organization collaboration
4. **Advanced Analytics**
   * Task completion analytics
   * Team productivity metrics
   * Predictive workload forecasting
   * Custom reporting and dashboards
5. **Mobile Optimization**
   * Progressive Web App (PWA) support
   * Mobile-first responsive design
   * Push notifications
   * Offline capability

## Time Spent

Approximately 3.5-4 hours