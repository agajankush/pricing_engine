import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from fastapi.responses import ORJSONResponse
import random

router = APIRouter()

class PricingRequest(BaseModel):
    product_id: str
    user_location: str
    is_prime_member: bool = False

class PriceDetail(BaseModel):
    product_id: str
    final_price: float
    source: str = 'live'

async def fetch_base_price(product_id: str) -> float:
    await asyncio.sleep(random.uniform(0.01, 0.05)) # Simulate slow db access
    return 49.99 + hash(product_id) % 10

async def fetch_market_data(user_location: str) -> float:
    await asyncio.sleep(random.uniform(0.02, 0.04)) # Simulate slow external API call
    return 0.95

@router.post("/price", response_class=ORJSONResponse)
async def get_dynamic_price(request: PricingRequest) -> PriceDetail:
    base_price, market_multiplier = await asyncio.gather(
        fetch_base_price(request.product_id),
        fetch_market_data(request.user_location)
    )
    
    discount = 0.05 if request.is_prime_member else 0.0
    final_price = round(base_price * market_multiplier * (1 - discount), 2)
    
    return PriceDetail(
        product_id=request.product_id,
        final_price=final_price
    )