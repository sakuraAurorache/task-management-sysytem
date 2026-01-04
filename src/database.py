from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from redis import Redis
from typing import Generator
import aioredis
from src.config import settings

# SQLAlchemy setup
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=20,
    max_overflow=10,
    echo=settings.debug
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Redis setup
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


# Async Redis setup
async def get_async_redis():
    redis = await aioredis.from_url(
        settings.redis_url,
        decode_responses=True,
        max_connections=10
    )
    try:
        yield redis
    finally:
        await redis.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis() -> Redis:
    return redis_client