from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from redis import Redis
from typing import Optional
import time

from src.database import engine, Base, get_db, get_redis
from src.config import settings
from src.api.v1 import tasks, users
# from src.utils.security import get_current_user
from src.models.user import User

# Create database tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    print("Starting up...")
    # Initialize database if needed
    # Perform any other startup operations

    yield

    # Shutdown
    print("Shutting down...")
    # Cleanup operations


app = FastAPI(
    title="Intelligent Task Management System",
    description="A backend API for managing tasks with intelligent features",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # In production, specify actual hosts
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Rate limiting middleware
async def rate_limit_middleware(request, call_next):
    # Simple rate limiting - in production use more sophisticated solution
    # like slowapi or fastapi-limiter
    redis = get_redis()
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"

    current = redis.get(key)
    if current and int(current) > settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )

    redis.incr(key, 1)
    redis.expire(key, 60)  # Reset every minute

    response = await call_next(request)
    return response


# Uncomment to enable rate limiting
# app.middleware("http")(rate_limit_middleware)



app.include_router(users.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Intelligent Task Management System API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/v1/health"
    }


@app.get("/api/status")
async def status():
    """API status endpoint."""
    return {
        "status": "operational",
        "timestamp": time.time(),
        "version": "1.0.0"
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return {
        "error": "Internal server error",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
    }