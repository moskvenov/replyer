from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache
from config import REDIS_URL
import asyncio

# Optional import for Redis
try:
    import redis.asyncio as redis
except ImportError:
    redis = None

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 10):
        self.limit = limit
        self.use_redis = False
        self.redis_client = None
        self.cache = None

        if REDIS_URL and redis:
            try:
                self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
                self.use_redis = True
                print("✅ Throttling: Using Redis")
            except Exception as e:
                print(f"⚠️ Redis Init Failed: {e}. Fallback to Memory.")
                self.use_redis = False
        
        if not self.use_redis:
            # Fallback
            self.cache = TTLCache(maxsize=10000, ttl=limit)

    async def __call__(self, handler, event: Message, data: dict):
        if not isinstance(event, Message):
            return await handler(event, data)
        
        user_id = event.from_user.id
        
        if self.use_redis:
            key = f"throttle:{user_id}"
            try:
                exists = await self.redis_client.get(key)
                if exists:
                    return # Throttled
                
                await self.redis_client.set(key, "1", ex=self.limit)
            except Exception as e:
                print(f"Redis Error: {e}")
                # Fail open or closed? Fail open (allow message) to not block user on db error
        else:
            if user_id in self.cache:
                return # Throttled
            self.cache[user_id] = True
            
        return await handler(event, data)
