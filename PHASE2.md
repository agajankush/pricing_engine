# High-Concurrency Dynamic Pricing Engine (Phase 2: Distributed Systems)

🎯 **Project Status:** Distributed Scale Achieved

This repository documents the architecture and implementation of the Dynamic Pricing Engine, which is engineered for ultra-low latency and high-volume traffic.

Phase 2 focuses on moving beyond single-server limits by introducing a decoupled, multi-container system using Redis for caching and Celery for background job processing. This transformation separates the fast customer read path from the slow background update path.

## 🏗️ Architectural Overview (Phase 2)

The system consists of three independent Dockerized services orchestrated by `docker-compose.yml`:

| Service    | Technology                 | Role                                                                                            | Scaling Concept Mastered    |
| ---------- | -------------------------- | ----------------------------------------------------------------------------------------------- | --------------------------- |
| **api**    | FastAPI (Gunicorn/Uvicorn) | Fast Read Path: Handles immediate customer requests (P95 latency target: < 50ms).               | Cache-Aside Pattern         |
| **redis**  | Redis (7-Alpine)           | Message Broker & Cache: Stores calculated prices and manages the Celery queue.                  | In-Memory Speed             |
| **worker** | Celery (Python)            | Slow Write Path: Executes long-running tasks (e.g., 5-second database scans) in the background. | Load Isolation / Decoupling |

### 1. High-Performance Decoupling Strategy

The key to Phase 2 is isolating the work that causes latency:

#### A. Cache-Aside Pattern (Ultra-Fast Read Path)

The API is engineered for speed by implementing the **Cache-Aside pattern** [cite: phase2.md]:

- **Cache Hit:** The API checks Redis first. If the price is available, it's returned in milliseconds, bypassing all slow I/O.
- **Pydantic Contract Integrity:** The API guarantees data conformity by explicitly re-validating the cached JSON data against the `PriceDetail` Pydantic model (`return PriceDetail(**json.loads(cached_data_str))`) before sending the response [cite: phase2.md].

#### B. Celery Decoupling (Load Isolation)

Long-running tasks, such as scanning the database for products that require an update, are delegated to the Celery worker [cite: phase2.md]:

- **Blocking Task:** The `recalculate_all_prices` job (simulating **$\mathbf{5}\mathbf{-second}$ blocking I/O**) is pushed to the Redis queue.
- **Zero Web Latency:** The `api` service immediately returns a `200 OK` response with a `task_id`, ensuring customer experience is never affected by the heavy background computation [cite: phase2.md].

### 2. Testing and Validation

To prove the success of the decoupling, follow this two-part test sequence:

#### A. Fast Read Test (Cache Validation)

This validates the effectiveness of the Cache-Aside Pattern.

1. **Cache Miss:** Send a `POST /api/v1/price` request for a new `product_id`. Result: Slow response (`"source": "database"`).
2. **Cache Hit:** Immediately repeat the request for the same ID. Result: Near-instantaneous response (`"source": "cache"`).

## ⚙️ How to Run the Distributed System

To run the entire three-service stack (FastAPI, Redis, Celery):

1. Ensure Docker is running and navigate to the project root.
2. Execute the Docker Compose build and run command:

   ```bash
   docker-compose up --build -d
   ```

   (The build process uses the single Dockerfile and the `docker-compose.yml` orchestrates the Gunicorn and Celery commands separately.)

3. Access API: http://localhost:8000/docs
4. Test Endpoint: `POST http://localhost:8000/api/v1/price`

**GitHub Repository Link:** https://github.com/agajankush/pricing_engine/tree/phase2
