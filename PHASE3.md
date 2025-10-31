## 🛡️ High-Concurrency Dynamic Pricing Engine (Phase 3: Production Resilience)

This document covers Phase 3 of the Dynamic Pricing Engine microservice, focusing on Resilience, Observability, and advanced architectural patterns. This phase upgrades the application from a fast, decoupled system into a robust, self-healing platform ready for production deployment.

### 🎯 Key Achievements in Phase 3

| Feature             | Concept Mastered        | Value                                                                                                                                             |
| ------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Distributed Tracing | OpenTelemetry / Jaeger  | Provides end-to-end visibility across the full request path (API → Redis → Worker), enabling instant diagnosis of latency spikes and bottlenecks. |
| Self-Healing Tasks  | Celery Auto-Retries     | Automatically retries on transient failures (e.g., ConnectionRefusedError, ExternalAPITimeout), preventing data loss and reducing manual ops.     |
| Concurrency Safety  | Redis Distributed Locks | Ensures idempotency and that the critical recalculation task runs on only one worker at a time, protecting data integrity at scale.               |
| Decoupling          | Redis Pub/Sub           | Replaces direct task submission with an event-driven architecture; external services can trigger updates without knowing Celery internals.        |

---

### 🔭 1. Testing End-to-End Observability

The system includes a full OpenTelemetry setup to trace requests across services/containers.

- **Instrumentation Points**:

  - **FastAPI API**: Starts the root span upon receiving the HTTP request.
  - **redis.asyncio**: Instruments cache lookups and the `PUBLISH` action.
  - **Celery Worker**: Picks up the trace context from the queue and spans the entire task execution (including simulated I/O like a 5-second database lookup).

- **Verification (Jaeger)**:
  - Access Jaeger UI: `http://localhost:16686`
  - Trigger the decoupled flow: `POST /api/v1/publish-market-event`
  - Inspect the trace timeline for the full path (API → Redis → Worker) and measure Python execution vs. queue wait time.

---

### 🛡️ 2. Resilience Implementation Details

#### A. Task Definition (`app/workers/tasks.py`)

The `recalculate_all_prices` task is configured for automated retries on failure.

```python
from app.workers.celery_app import celery_app
from app.core.exceptions import ExternalAPITimeout

@celery_app.task(
    # Catches defined and built-in exceptions for auto-retrying
    autoretry_for=(ConnectionRefusedError, ExternalAPITimeout),
    retry_kwargs={"max_retries": 5, "countdown": 30},
    acks_late=True,
)

def recalculate_all_prices():
    # ... core logic that may raise transient errors ...
    # On handled exception paths, Celery will automatically retry per config
    # or you may explicitly call: raise self.retry(exc=exc)
    pass
```

#### B. Distributed Locking (`app/workers/tasks.py`)

The task uses a Redis lock to ensure concurrency safety when running the price update logic.

```python
from app.services.cache import get_redis_client_sync


def recalculate_all_prices():
    redis_client = get_redis_client_sync()
    LOCK_NAME = "recalculate_gloabl_lock"  # deliberate global lock name

    with redis_client.lock(LOCK_NAME, timeout=60) as lock_acquired:
        if lock_acquired:
            # ONLY ONE worker proceeds here
            # ... critical update logic ...
            return {"status": "updated"}
        else:
            return {"status": "skipped"}
```

---

### 🐳 Docker Compose Architecture (Phase 3 Services)

All services are orchestrated via Docker Compose.

| Service  | Role                              | Command/Image                                 |
| -------- | --------------------------------- | --------------------------------------------- |
| redis    | Cache & Celery Broker/Backend     | Image: `redis:7-alpine`                       |
| jaeger   | Trace Collector & Visualization   | Image: `jaegertracing/all-in-one:latest`      |
| api      | Fast Read Path (Gunicorn/FastAPI) | Command: `gunicorn ... -c gunicorn_config.py` |
| worker   | Task Execution (Celery)           | Command: `python -m celery -A ... worker`     |
| listener | Pub/Sub Event Bridge              | Command: `python -m app.workers.listener`     |

---

### 🔗 GitHub Repository

Repository: https://github.com/agajankush/pricing_engine/tree/phase3

---

### ✅ How to Validate Phase 3 Quickly

1. Start the stack (Docker Compose) and confirm all services are healthy.
2. Open Jaeger at `http://localhost:16686`.
3. Hit the API endpoint `POST /api/v1/publish-market-event`.
4. Observe a single coherent trace spanning API → Redis → Worker.
5. Temporarily induce a transient failure (e.g., block external dependency) to watch Celery auto-retries.
6. Trigger concurrent events and confirm the distributed lock prevents overlapping critical sections.

---

### 📌 Notes

- Traces propagate across API → Redis → Celery ensuring full visibility.
- Auto-retry policy avoids manual intervention for transient incidents.
- Distributed locking protects data integrity under high concurrency.
- Pub/Sub decoupling enables other microservices to integrate without direct task coupling.
