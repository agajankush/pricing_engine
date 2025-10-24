from app.core.config import settings
from prometheus_client import multiprocess
import os, shutil

# Deployment Settings
bind = f"{settings.HOST}:{settings.PORT}"
workers = settings.WORKERS
worker_class = "uvicorn.workers.UvicornWorker"
prometheus_dir = "/tmp/prom_multiprocess"

# Gunicorn Hook 1
# Runs once before server starup
def on_starting(server):
    # Clear old metrics and ensure the shared directory exists
    if os.path.isdir(prometheus_dir):
        shutil.rmtree(prometheus_dir)
    os.makedirs(prometheus_dir)

# Gunicorn Hook 2
# Runs before a worker process is forked
def pre_load(worker):
    # Sets the prometheus dir telling every worker where to write the metrics data
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = prometheus_dir

# Gunicorn Hook 3 
# Runs when a worker gracefully exists
def child_exit(server, worker):
    # Removed the dead workers metrics file, ensuring the Collector doesnt report stale data
    multiprocess.mark_process_dead(worker.pid)