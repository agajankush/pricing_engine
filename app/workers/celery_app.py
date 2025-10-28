from celery import Celery
from app.core.config import settings
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from app.core.tracing import configure_tracer

celery_app = Celery(
    'pricing_tasks',
    broker=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0',
    backend=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1',
)

# OpenTelemetry Tracer Configuration
configure_tracer("pricing-worker-service")
# Celery Instrumentation
CeleryInstrumentor(celery_app).instrument()
