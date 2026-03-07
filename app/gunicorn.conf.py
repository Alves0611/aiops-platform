import os
import shutil

bind = "0.0.0.0:8080"
workers = 2
threads = 4
accesslog = None  # Access logging handled by Flask after_request
errorlog = "-"

# --- Prometheus multiprocess setup ---
prometheus_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR", "/tmp/prometheus_multiproc")
os.makedirs(prometheus_dir, exist_ok=True)


def on_starting(server):
    if os.path.isdir(prometheus_dir):
        shutil.rmtree(prometheus_dir)
    os.makedirs(prometheus_dir, exist_ok=True)


def child_exit(server, worker):
    from prometheus_client import multiprocess
    multiprocess.mark_process_dead(worker.pid)


# --- JSON logging for Gunicorn's own loggers ---
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            "rename_fields": {"asctime": "timestamp", "levelname": "level"},
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    "loggers": {
        "gunicorn.error": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "gunicorn.access": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}
