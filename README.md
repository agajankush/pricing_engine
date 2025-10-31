# 💰 High-Concurrency Dynamic Pricing Engine

This repository details the architecture and implementation of a scalable microservice built with FastAPI, Redis, Celery, and OpenTelemetry. The project demonstrates mastery of advanced Python scaling concepts, moving from local optimization to a fully decoupled, self-healing distributed system.

**GitHub Repository**: https://github.com/agajankush/pricing_engine/

---

## 🚀 Architectural Journey: Phase-by-Phase Scaling

The project was executed in three distinct phases, addressing critical bottlenecks at each level of scale.

### Phase 1: Single-Server Performance Optimization

**Goal**: Maximize throughput on a single server by eliminating Python/GIL bottlenecks and latency.

| Scaling Challenge      | Solution Implemented                           | Primary Goal                                                                              |
| ---------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------- |
| I/O Bottleneck         | Asynchronous Concurrency with `asyncio.gather` | Minimize I/O wait time by running data lookups simultaneously.                            |
| Serialization Overhead | ORJSONResponse Integration                     | Eliminate CPU waste by using a Rust-optimized JSON encoder (20%-50% throughput increase). |
| CPU/GIL Limit          | Gunicorn Multi-Worker Parallelism              | Utilize all available CPU cores to multiply throughput capacity.                          |
| System Visibility      | Prometheus Timing Middleware                   | Track the critical P95 latency accurately under load.                                     |

**Key Achievements**:

- **I/O Concurrency**: Runs simultaneous I/O operations concurrently, reducing request latency from ~500ms (sequential sum of multiple operations) to ~100ms (concurrent maximum).
- **Parallelism**: Uses multiple Uvicorn worker processes to bypass the GIL and fully utilize all CPU cores.
- **Validation**: Achieved stable P95 latency under concurrent load, confirming architecture effectiveness.

#### Setup and Installation (Phase 1)

**Prerequisites**:

- Python 3.10+
- Docker (Optional, but recommended for full testing)

**Running in Parallel Mode (Production Setup)**:

```bash
# This command launches multiple Uvicorn workers and enables metric aggregation
gunicorn app.main:app -c gunicorn_config.py
```

**Verifying Observability**:

- **API Docs**: http://localhost:8000/docs
- **Metrics Feed**: http://localhost:8000/metrics

**Integration Test (Locust)**:

```bash
locust -f locustfile.py --host http://localhost:8000
```

**Validation Criteria**:
| Metric | Goal | Proof of Success |
| ----------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------ |
| P95 Latency (95th Percentile) | Maintain latency below 150ms | Proves the asyncio.gather I/O concurrency model prevented requests from queuing up. |
| Failure Rate | Must remain at 0% | Proves the Gunicorn/Uvicorn multi-process setup is resilient and stable under heavy concurrency. |

---

### Phase 2: Decoupling and Distributed Caching

**Goal**: Isolate the fast customer read path from the slow business update path to maintain ultra-low latency reads.

**Architectural Overview**: The system consists of three independent Dockerized services orchestrated by `docker-compose.yml`:

| Service    | Technology                 | Role                                                                                            | Scaling Concept Mastered    |
| ---------- | -------------------------- | ----------------------------------------------------------------------------------------------- | --------------------------- |
| **api**    | FastAPI (Gunicorn/Uvicorn) | Fast Read Path: Handles immediate customer requests (P95 latency target: < 50ms).               | Cache-Aside Pattern         |
| **redis**  | Redis (7-Alpine)           | Message Broker & Cache: Stores calculated prices and manages the Celery queue.                  | In-Memory Speed             |
| **worker** | Celery (Python)            | Slow Write Path: Executes long-running tasks (e.g., 5-second database scans) in the background. | Load Isolation / Decoupling |

#### High-Performance Decoupling Strategy

**A. Cache-Aside Pattern (Ultra-Fast Read Path)**

- **Cache Hit**: The API checks Redis first. If the price is available, it's returned in milliseconds (< 5ms latency), bypassing all slow I/O.
- **Pydantic Contract Integrity**: The API guarantees data conformity by explicitly re-validating the cached JSON data against the `PriceDetail` Pydantic model before sending the response.

**B. Celery Decoupling (Load Isolation)**

- **Blocking Task**: The `recalculate_all_prices` job (simulating **5-second blocking I/O**) is pushed to the Redis queue.
- **Zero Web Latency**: The `api` service immediately returns a `200 OK` response with a `task_id`, ensuring customer experience is never affected by the heavy background computation.

#### Testing and Validation (Phase 2)

**Fast Read Test (Cache Validation)**:

1. **Cache Miss**: Send a `POST /api/v1/price` request for a new `product_id`. Result: Slow response (`"source": "database"`).
2. **Cache Hit**: Immediately repeat the request for the same ID. Result: Near-instantaneous response (`"source": "cache"`).

**Key Achievements**:

- **Fast Read Path**: Serves prices from in-memory Redis (< 5ms latency) after the initial calculation, reducing database load.
- **Slow Write Path**: Offloads complex, long-running tasks to isolated worker processes.
- **Process Isolation**: Docker Compose manages independent containers, ensuring complete separation of concerns.

---

### 🛡️ Phase 3: Resilience, Observability, and Event-Driven Architecture

**Goal**: Build a production-ready system that is self-healing, safe against race conditions, and fully traceable across all container boundaries.

| Feature             | Concept Mastered        | Value                                                                                                                                             |
| ------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Distributed Tracing | OpenTelemetry / Jaeger  | Provides end-to-end visibility across the full request path (API → Redis → Worker), enabling instant diagnosis of latency spikes and bottlenecks. |
| Self-Healing Tasks  | Celery Auto-Retries     | Automatically retries on transient failures (e.g., ConnectionRefusedError, ExternalAPITimeout), preventing data loss and reducing manual ops.     |
| Concurrency Safety  | Redis Distributed Locks | Ensures idempotency and that the critical recalculation task runs on only one worker at a time, protecting data integrity at scale.               |
| Event-Driven Flow   | Redis Pub/Sub           | Replaces direct, coupled submission with a fully asynchronous event listener, enabling external microservices to trigger updates seamlessly.      |

#### Testing End-to-End Observability

The system includes a full OpenTelemetry setup to trace requests across services/containers.

**Instrumentation Points**:

- **FastAPI API**: Starts the root span upon receiving the HTTP request.
- **redis.asyncio**: Instruments cache lookups and the `PUBLISH` action.
- **Celery Worker**: Picks up the trace context from the queue and spans the entire task execution (including simulated I/O like a 5-second database lookup).

**Verification (Jaeger)**:

- Access Jaeger UI: `http://localhost:16686`
- Trigger the decoupled flow: `POST /api/v1/publish-market-event`
- Inspect the trace timeline for the full path (API → Redis → Worker) and measure Python execution vs. queue wait time.

#### Resilience Implementation Details

**A. Task Definition (`app/workers/tasks.py`)**

The `recalculate_all_prices` task is configured for automated retries on failure:

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

**B. Distributed Locking (`app/workers/tasks.py`)**

The task uses a Redis lock to ensure concurrency safety:

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

## 🛠️ Deployment and Validation

The entire architecture is defined in `docker-compose.yml`, orchestrating all necessary services.

### Services

| Service  | Role                              | Command/Image                                 |
| -------- | --------------------------------- | --------------------------------------------- |
| api      | Fast Read Path (Gunicorn/FastAPI) | Command: `gunicorn ... -c gunicorn_config.py` |
| redis    | Cache & Celery Broker/Backend     | Image: `redis:7-alpine`                       |
| worker   | Task Execution (Celery)           | Command: `python -m celery -A ... worker`     |
| listener | Pub/Sub Event Bridge              | Command: `python -m app.workers.listener`     |
| jaeger   | Trace Collector & UI              | Image: `jaegertracing/all-in-one:latest`      |

### Running the System

To run the entire distributed stack:

```bash
docker-compose up --build -d
```

**Access Points**:

- **API Docs**: http://localhost:8000/docs
- **Jaeger UI**: http://localhost:16686
- **Metrics**: http://localhost:8000/metrics

### Key Validation Tests

| Test              | Endpoint / UI                       | Success Criteria                                                                                 |
| ----------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------ |
| Fast Read Path    | `POST /api/v1/price`                | Latency drops to < 5ms on the second request (Cache Hit).                                        |
| Event-Driven Flow | `POST /api/v1/publish-market-event` | Listener log shows event receipt; Worker log shows task execution after the API call completes.  |
| Observability     | http://localhost:16686              | Traces show the full path: api-service → redis → worker-service unified under a single Trace ID. |

### Phase 3 Quick Validation Checklist

1. Start the stack (Docker Compose) and confirm all services are healthy.
2. Open Jaeger at `http://localhost:16686`.
3. Hit the API endpoint `POST /api/v1/publish-market-event`.
4. Observe a single coherent trace spanning API → Redis → Worker.
5. Temporarily induce a transient failure (e.g., block external dependency) to watch Celery auto-retries.
6. Trigger concurrent events and confirm the distributed lock prevents overlapping critical sections.

---

## 📌 Key Takeaways

- **Phase 1**: Achieved ultra-low latency and maximum throughput on a single server through I/O concurrency, parallelism, and optimized serialization.
- **Phase 2**: Decoupled fast read paths from slow write paths using Redis caching and Celery task queues, enabling horizontal scaling.
- **Phase 3**: Transformed into a production-ready, self-healing system with distributed tracing, auto-retries, distributed locks, and event-driven architecture.

---

## 📚 Additional Documentation

For detailed implementation details by phase:

- [PHASE1.md](./PHASE1.md) - Single-server optimization details
- [PHASE2.md](./PHASE2.md) - Distributed caching and decoupling
- [PHASE3.md](./PHASE3.md) - Production resilience and observability
