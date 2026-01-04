from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "mysql+pymysql://root:123456@localhost:3306/taskdb"
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "dev-secret-key-for-testing-only"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Application
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # Caching
    cache_ttl: int = 300  # 5 minutes

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()