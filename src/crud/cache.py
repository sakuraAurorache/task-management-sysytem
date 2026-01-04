from redis import Redis
from typing import Optional, Any
import json
import pickle
from datetime import timedelta


class CacheManager:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        data = self.redis.get(key)
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return pickle.loads(data)
        return None

    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL"""
        try:
            data = json.dumps(value)
        except (TypeError, OverflowError):
            data = pickle.dumps(value)

        self.redis.setex(key, timedelta(seconds=ttl), data)

    def delete(self, key: str):
        """Delete value from cache"""
        self.redis.delete(key)

    def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)

    def clear_task_cache(self, task_id: Optional[int] = None):
        """Clear task-related cache"""
        if task_id:
            # Clear specific task cache
            self.delete(f"task:{task_id}")
            self.delete(f"task_dependencies:{task_id}")
        # Clear task list cache
        self.delete_pattern("tasks:*")

    def get_or_set(self, key: str, func, ttl: int = 300) -> Any:
        """Get from cache or set using function"""
        cached = self.get(key)
        if cached is not None:
            return cached

        result = func()
        self.set(key, result, ttl)
        return result