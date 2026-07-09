import redis.asyncio as aioredis

from app.core.config import settings

# Pool único del proceso; decode_responses para trabajar con str directamente.
redis_client: aioredis.Redis = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


def get_redis() -> aioredis.Redis:
    return redis_client
