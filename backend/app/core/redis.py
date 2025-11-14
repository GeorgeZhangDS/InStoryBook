"""
Redis connection management
"""
import redis.asyncio as aioredis
from typing import Optional
from functools import lru_cache

from app.core.config import settings


class RedisClient:
    """Redis async client wrapper"""
    
    def __init__(self):
        self._client: Optional[aioredis.Redis] = None
    
    async def connect(self):
        """Initialize Redis connection"""
        if self._client is None:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self._client = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self._client.ping()
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None
    
    @property
    def client(self) -> aioredis.Redis:
        """Get Redis client instance"""
        if self._client is None:
            raise RuntimeError("Redis client not initialized. Call connect() first.")
        return self._client


@lru_cache()
def get_redis() -> RedisClient:
    """Get Redis client singleton"""
    return RedisClient()

