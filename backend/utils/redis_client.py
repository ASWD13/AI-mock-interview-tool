"""Redis client utility."""

import json
import redis.asyncio as aioredis
from typing import Optional, Any
from backend.config import get_settings


class RedisClient:
    """Async Redis client wrapper."""

    def __init__(self):
        self._client: Optional[aioredis.Redis] = None

    async def connect(self):
        """Initialize Redis connection."""
        settings = get_settings()
        self._client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )

    async def disconnect(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()

    @property
    def client(self) -> aioredis.Redis:
        if self._client is None:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

    async def set_json(self, key: str, value: Any, expire: int = 3600):
        """Store JSON-serializable data."""
        await self.client.set(key, json.dumps(value, default=str), ex=expire)

    async def get_json(self, key: str) -> Optional[Any]:
        """Retrieve JSON data."""
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None

    async def delete(self, key: str):
        """Delete a key."""
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.client.exists(key) > 0


# Singleton
redis_client = RedisClient()
