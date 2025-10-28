from app.workers.celery_app import celery_app
from app.services.cache import set_cached_price
from app.workers.tasks_utils import fetch_all_product_ids, calculate_price

@celery_app.task(acks_late=True)
async def recalculate_all_prices():
    """
    Long running taks to fetch all producsts, recalculate price and update the cache.
    This task is executed entirely outside the FastAPI web process.
    """
    
    product_ids = fetch_all_product_ids()
    
    updated_count = 0
    for product_id in product_ids:
        price_data = calculate_price(product_id)
        await set_cached_price(product_id, price_data)
        updated_count += 1
    
    return {
        'status': 'success',
        'updated_count': updated_count
    }