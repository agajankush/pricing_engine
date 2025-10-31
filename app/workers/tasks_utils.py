import time
import random
from typing import List

def fetch_all_product_ids() -> List[str]:
    """
    Simulates detching all product ids from a slow database query
    This is a long-running, blocking I/O task
    """
    
    time.sleep(5)
    
    return [f"P-{random.randint(100, 999)}" for _ in range(1000)]

def calculate_price(product_id: str) -> dict:
    """
    Simulates calculating the price for a product
    This is a long-running, blocking I/O task
    """
    
    time.sleep(0.01)
    
    base_price = 49.99 + hash(product_id) % 10
    market_multiplier = random.uniform(0.9, 1.1)
    discount = 0.10
    final_price = round(base_price * market_multiplier * (1 - discount), 2)
    
    return {
        'product_id': product_id,
        'final_price': final_price,
        'base_price': base_price,
        'discount_rate': discount,
        'source': 'proactive_worker'
    }