High-Concurrency Dynamic Pricing Engine (Phase 1: Single-Server Scale)

This repository contains the Phase 1 implementation of a High-Concurrency Dynamic Pricing Engine built on FastAPI. The primary goal of this phase was to achieve ultra-low latency and maximum throughput on a single machine by rigorously optimizing I/O concurrency, data serialization, and multi-core parallelism.

## 🎯 Phase 1 Focus: Single-Server Performance Optimization

This phase validates the ability of the microservice to handle massive concurrent traffic before moving to distributed systems.

| Scaling Challenge      | Solution Implemented                         | Primary Goal                                                     |
| ---------------------- | -------------------------------------------- | ---------------------------------------------------------------- |
| I/O Bottleneck         | Asynchronous Concurrency with asyncio.gather | Minimize I/O wait time by running data lookups simultaneously.   |
| Serialization Overhead | ORJSONResponse Integration                   | Eliminate CPU waste by using a Rust-optimized JSON encoder.      |
| CPU/GIL Limit          | Gunicorn Multi-Worker Parallelism            | Utilize all available CPU cores to multiply throughput capacity. |
| System Visibility      | Prometheus Timing Middleware                 | Track the critical P95 latency accurately under load.            |

## 🛠️ Setup and Installation

### Prerequisites

- Python 3.10+
- Docker (Optional, but recommended for full testing)

### 1. Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/agajankush/pricing_engine
cd pricing_engine
pip install -r requirements.txt
```

### 2. Running in Parallel Mode (Production Setup)

To test the multi-core scaling strategy, you must run the application using Gunicorn and its configuration file, which activates the parallel workers and Prometheus hooks.

```bash
# This command launches multiple Uvicorn workers and enables metric aggregation
gunicorn app.main:app -c gunicorn_config.py
```

The number of workers is defined in `app/core/config.py`.

### 3. Verifying Observability

Access the following endpoints to confirm the monitoring setup is active:

- **API Docs**: http://localhost:8000/docs
- **Metrics Feed**: http://localhost:8000/metrics

**Verification**: Running `curl http://localhost:8000/metrics` should output aggregated metrics (`http_request_duration_seconds_bucket`) from all running Gunicorn workers.

## 📈 Integration Test (The Moment of Truth)

This test proves that the combination of concurrency (Step 2) and parallelism (Step 4) successfully maintains low latency under high load.

### Test Tool: Locust

The `locustfile.py` simulates numerous users concurrently requesting price scores, forcing maximum I/O pressure on the system.

### Execution

1. Ensure the server is running with Gunicorn (as above).
2. Start the Locust client in a separate terminal:

```bash
locust -f locustfile.py --host http://localhost:8000
```

3. Open the Locust UI at http://localhost:8089.

### Validation and Success Criteria

| Metric                        | Goal                         | Proof of Success                                                                                 |
| ----------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------ |
| P95 Latency (95th Percentile) | Maintain latency below 150ms | Proves the asyncio.gather I/O concurrency model prevented requests from queuing up.              |
| Failure Rate                  | Must remain at 0%            | Proves the Gunicorn/Uvicorn multi-process setup is resilient and stable under heavy concurrency. |

If this validation passes, Phase 1 is complete, and the microservice is ready to be decoupled in Phase 2.

**GitHub Repository Link**: https://github.com/agajankush/pricing_engine
