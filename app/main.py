from fastapi import FastAPI
from fastapi.responses import ORJSONResponse, PlainTextResponse
from app.routes import pricing
from app.core.config import settings
from prometheus_client import generate_latest, CollectorRegistry, multiprocess
from starlette.responses import PlainTextResponse
import os

app = FastAPI(
    title=settings.APP_NAME,
    default_response_class=ORJSONResponse
)

app.include_router(pricing.router, prefix="/api/v1")

# Adding the timing middleware on all the routes of the application
if settings.ENABLE_METRICS:
    from app.core.middleware import TimingMiddleware
    app.add_middleware(TimingMiddleware)

def create_multiprocess_registry():
    # This registry correctly aggregates metrics from all processes
    registry = CollectorRegistry()
    # The MultiprocessCollector reads all individual metric files created byt the workers.
    multiprocess.MultiProcessCollector(registry)
    return registry

@app.get('/metrics', reponse_class=PlainTextResponse, include_in_schema=False)
def metrics():
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        registry = create_multiprocess_registry()
    else:
        registry = CollectorRegistry()

    return generate_latest(registry)