from app.workers.celery_app import celery_app
# from app.services.cache import set_cached_price, get_redis_client_sync
from app.services.cache import set_cached_price_sync, get_redis_client_sync
from app.workers.tasks_utils import fetch_all_product_ids, calculate_price
import random 

class ExternalAPITimeout(Exception):
    """Custom exception raised for transient external API timeouts."""
    pass

LOCK_NAME = "recalculate_gloabl_lock"
LOCK_TIMEOUT = 60

@celery_app.task(
    autoretry_for=(ConnectionRefusedError, ExternalAPITimeout),
    retry_kwargs={'max_retries': 5, 'countdown': 30},
    acks_late=True
)
def recalculate_all_prices():
    """
    Long running taks to fetch all producsts, recalculate price and update the cache.
    This task is executed entirely outside the FastAPI web process.
    """
    r = get_redis_client_sync()
    
    with r.lock(LOCK_NAME, timeout=LOCK_TIMEOUT) as lock_acquired:
        if lock_acquired:
            try:
                if random.random() < 0.1:
                    raise ExternalAPITimeout("External API timeout")
                
                product_ids = fetch_all_product_ids()
                
                updated_count = 0
                for product_id in product_ids:
                    price_data = calculate_price(product_id)
                    set_cached_price_sync(product_id, price_data)
                    updated_count += 1
                
                return {
                    'status': 'success',
                    'updated_count': updated_count
                }
            except ExternalAPITimeout as exc:
                print(f"External API Timeout encountered: {exc}. Retrying in 30 seconds...")
                raise recalculate_all_prices.retry(exc=exc)
        else:
            print("LOCK FAILED: Another recalculation is already in progress. Skipping...")
            return {"status": "skipped", "reason": "lock_help_by_another_worker"}