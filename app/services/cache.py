import redis.asyncio as redis
import json
from app.core.config import settings
import redis as redis_sync


async def get_redis_client():
    return redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

async def get_cached_price(client: redis.Redis, product_id: str):
    return await client.get(f"price:{product_id}")

async def set_cached_price(client: redis.Redis, product_id: str, price_data: dict):
    await client.set(f"price:{product_id}", json.dumps(price_data), px=60000)

def get_redis_client_sync():
    return redis_sync.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

def set_cached_price_sync(product_id: str, price_data: dict):
    client = get_redis_client_sync()
    client.set(f"price:{product_id}", json.dumps(price_data), px=60000)
