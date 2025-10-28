import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.responses import ORJSONResponse
import random
from typing import Annotated
from app.services.cache import get_redis_client, get_cached_price, set_cached_price
import redis.asyncio as redis
import json

RedisClient = Annotated[redis.Redis, Depends(get_redis_client)]
router = APIRouter()

class PricingRequest(BaseModel):
    product_id: str
    user_location: str
    is_prime_member: bool = False

class PriceDetail(BaseModel):
    product_id: str
    final_price: float
    base_price: float
    discount_rate: float
    source: str = 'live'

async def fetch_base_price(product_id: str) -> float:
    await asyncio.sleep(random.uniform(0.01, 0.05)) # Simulate slow db access
    return 49.99 + hash(product_id) % 10

async def fetch_market_data(user_location: str) -> float:
    await asyncio.sleep(random.uniform(0.02, 0.04)) # Simulate slow external API call
    return 0.95

@router.post("/price", response_class=ORJSONResponse)
async def get_dynamic_price(request: PricingRequest, cache: RedisClient) -> PriceDetail:
    
    cached_price = await get_cached_price(cache, request.product_id)
    
    if cached_price:
        price_data_dict = json.loads(cached_price)
        price_data_dict['source'] = 'cache'
        return PriceDetail(**price_data_dict)
    
    base_price, market_multiplier = await asyncio.gather(
        fetch_base_price(request.product_id),
        fetch_market_data(request.user_location)
    )
    
    discount = 0.05 if request.is_prime_member else 0.0
    final_price = round(base_price * market_multiplier * (1 - discount), 2)
    
    response_data_dict = {
        'product_id': request.product_id,
        'final_price': final_price,
        'base_price': base_price,
        'discount_rate': discount,
        'source': 'database'
    }
    await set_cached_price(cache, request.product_id, response_data_dict)
    return PriceDetail(**response_data_dict)