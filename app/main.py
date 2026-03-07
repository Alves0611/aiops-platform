import os
import time
import threading
import random
import string
import logging
import uuid
import requests
from flask import Flask, render_template, jsonify, request, g
from prometheus_client import (
    Counter, Histogram, generate_latest, CollectorRegistry,
    multiprocess, CONTENT_TYPE_LATEST,
)
from pythonjsonlogger.json import JsonFormatter

app = Flask(__name__)

# --- Structured JSON Logging ---
json_formatter = JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"asctime": "timestamp", "levelname": "level"},
)
log_handler = logging.StreamHandler()
log_handler.setFormatter(json_formatter)

app.logger.handlers.clear()
app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)
app.logger.propagate = False

logging.root.handlers.clear()
logging.root.addHandler(log_handler)
logging.root.setLevel(logging.INFO)

logger = app.logger

# --- Prometheus Metrics ---
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)


@app.before_request
def before_request_hook():
    g.start_time = time.time()
    g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))


@app.after_request
def after_request_hook(response):
    if request.path == "/metrics":
        return response

    duration = time.time() - g.get("start_time", time.time())
    method = request.method
    endpoint = request.url_rule.rule if request.url_rule else request.path
    status = str(response.status_code)

    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

    logger.info(
        "request completed",
        extra={
            "request_id": g.get("request_id", ""),
            "method": method,
            "path": endpoint,
            "status": response.status_code,
            "duration": round(duration, 4),
            "remote_addr": request.remote_addr,
        },
    )

    return response


@app.route("/metrics")
def metrics():
    if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        data = generate_latest(registry)
    else:
        data = generate_latest()
    return data, 200, {"Content-Type": CONTENT_TYPE_LATEST}

# Global state for background traffic simulation
traffic_state = {
    "running": False,
    "threads": 0,
    "rps": 0,
    "target_url": "",
    "stats": {"total_requests": 0, "errors": 0, "success": 0},
    "stop_event": threading.Event(),
}
stats_lock = threading.Lock()


@app.route("/")
def index():
    return render_template("index.html")


# --- Intentional Error Endpoints ---

@app.route("/api/error/500")
def error_500():
    """Return an internal server error."""
    return jsonify({"error": "Internal Server Error (intentional)"}), 500


@app.route("/api/error/timeout")
def error_timeout():
    """Simulate a request timeout."""
    delay = min(int(request.args.get("seconds", 30)), 120)
    time.sleep(delay)
    return jsonify({"message": f"Responded after {delay}s delay"})


@app.route("/api/error/crash")
def error_crash():
    """Raise an unhandled exception."""
    raise RuntimeError("Intentional crash for testing")


@app.route("/api/error/oom")
def error_oom():
    """Simulate high memory usage by allocating a large list."""
    size_mb = int(request.args.get("mb", 100))
    data = "x" * (size_mb * 1024 * 1024)
    return jsonify({"message": f"Allocated ~{size_mb}MB", "length": len(data)})


@app.route("/api/error/cascade")
def error_cascade():
    """Generate a cascade of errors (random 4xx/5xx)."""
    count = int(request.args.get("count", 5))
    codes = [400, 401, 403, 404, 429, 500, 502, 503]
    results = []
    for _ in range(count):
        code = random.choice(codes)
        results.append({"status_code": code, "message": f"Simulated {code}"})
    chosen = random.choice(codes)
    return jsonify({"errors": results}), chosen


# --- CPU / Resource Stress ---

@app.route("/api/stress/cpu")
def stress_cpu():
    """Burn CPU for a given duration."""
    duration = int(request.args.get("seconds", 5))
    end = time.time() + duration
    iterations = 0
    while time.time() < end:
        _ = sum(i * i for i in range(1000))
        iterations += 1
    return jsonify({"message": f"CPU stress for {duration}s", "iterations": iterations})


# --- Health & Info ---

@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy",
        "hostname": os.environ.get("HOSTNAME", "unknown"),
        "pod_name": os.environ.get("POD_NAME", "unknown"),
        "node_name": os.environ.get("NODE_NAME", "unknown"),
    })


@app.route("/api/info")
def info():
    return jsonify({
        "hostname": os.environ.get("HOSTNAME", "unknown"),
        "pod_name": os.environ.get("POD_NAME", "unknown"),
        "node_name": os.environ.get("NODE_NAME", "unknown"),
        "cpu_request": os.environ.get("CPU_REQUEST", "unknown"),
        "memory_request": os.environ.get("MEM_REQUEST", "unknown"),
    })


# --- Traffic Generator ---

def _send_requests(target_url, rps, stop_event):
    """Worker thread that sends requests at a given rate."""
    interval = 1.0 / rps if rps > 0 else 1.0
    while not stop_event.is_set():
        try:
            resp = requests.get(target_url, timeout=10)
            with stats_lock:
                traffic_state["stats"]["total_requests"] += 1
                if resp.status_code >= 400:
                    traffic_state["stats"]["errors"] += 1
                else:
                    traffic_state["stats"]["success"] += 1
        except Exception:
            with stats_lock:
                traffic_state["stats"]["total_requests"] += 1
                traffic_state["stats"]["errors"] += 1
        time.sleep(interval)


@app.route("/api/traffic/start", methods=["POST"])
def traffic_start():
    """Start generating traffic to a target URL."""
    if traffic_state["running"]:
        return jsonify({"error": "Traffic generator already running"}), 409

    data = request.get_json()
    target_url = data.get("target_url", "http://localhost:8080/api/health")
    rps = int(data.get("rps", 10))
    threads = int(data.get("threads", 2))

    traffic_state["stop_event"] = threading.Event()
    traffic_state["running"] = True
    traffic_state["rps"] = rps
    traffic_state["threads"] = threads
    traffic_state["target_url"] = target_url
    traffic_state["stats"] = {"total_requests": 0, "errors": 0, "success": 0}

    rps_per_thread = max(1, rps // threads)
    for _ in range(threads):
        t = threading.Thread(
            target=_send_requests,
            args=(target_url, rps_per_thread, traffic_state["stop_event"]),
            daemon=True,
        )
        t.start()

    return jsonify({"message": f"Started {threads} threads at ~{rps} rps to {target_url}"})


@app.route("/api/traffic/stop", methods=["POST"])
def traffic_stop():
    """Stop the traffic generator."""
    if not traffic_state["running"]:
        return jsonify({"error": "Traffic generator not running"}), 409

    traffic_state["stop_event"].set()
    traffic_state["running"] = False
    return jsonify({"message": "Traffic stopped", "stats": traffic_state["stats"]})


@app.route("/api/traffic/status")
def traffic_status():
    return jsonify({
        "running": traffic_state["running"],
        "target_url": traffic_state["target_url"],
        "rps": traffic_state["rps"],
        "threads": traffic_state["threads"],
        "stats": traffic_state["stats"],
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
