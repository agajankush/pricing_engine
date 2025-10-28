from celery import Celery
from app.core.config import settings

celery_app = Celery(
    'pricing_tasks',
    broker=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0',
    backend=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1',
)