import json
import logging
import os
from pathlib import Path
from urllib.parse import unquote
import yaml
import time
from flask import Flask, request, jsonify, url_for, Response, render_template
from prometheus_client import generate_latest, REGISTRY, CollectorRegistry, \
    multiprocess
from prometheus_client import Counter, Gauge
from task_manager.worker import app as celery_app
import sys
from flask_cors import CORS
# Update import for Sentinel functionality
from redis.sentinel import Sentinel
import redis
from functools import lru_cache

from subscription_manager import (
    init_subscribers, load_config, persist_config, shutdown, SUBSCRIBERS
)

# set up logging
log_formatter = logging.Formatter(
    fmt='%(asctime)s.%(msecs)03dZ, %(name)s, %(levelname)s, %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S'
)
log_formatter.converter = time.gmtime

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(log_formatter)

root_logger = logging.getLogger()
root_logger.setLevel(os.getenv("LOG_LEVEL", "DEBUG").upper())

# Clear existing handlers and add our stream handler
if root_logger.hasHandlers():
    root_logger.handlers.clear()
root_logger.addHandler(stream_handler)

LOGGER = logging.getLogger(__name__)

DATA_DIRECTORY = Path(
    os.getenv("DATA_BASEPATH", "/data/wis2-downloads")).resolve()


def get_json() -> dict:
    """Get JSON body safely."""
    if not request.is_json:
        return {}
    return request.get_json(silent=True) or {}


def normalise_topic(value: str | None) -> str | None:
    """Normalise/validate topic values from request path or payload."""
    if value is None:
        return None
    value = unquote(value).strip()
    return value or None


def normalise_path(userpath: str) -> str | None:
    if not userpath:
        return None

    resolved_path = (DATA_DIRECTORY / userpath).resolve()

    if (DATA_DIRECTORY not in resolved_path.parents and
            resolved_path != DATA_DIRECTORY):
        return None

    return str(resolved_path.relative_to(DATA_DIRECTORY))


# Load config
CONFIG = load_config()

# Initialise subscribers and topics
init_subscribers(CONFIG)

# Persist config
persist_config(CONFIG)

# Now set up flask app
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev')
if FLASK_SECRET_KEY == 'dev':
    LOGGER.warning("Using insecure secret key for flask app")
app = Flask(__name__, instance_relative_config=True)
app.config.from_mapping(SECRET_KEY=FLASK_SECRET_KEY)

# --- Redis Sentinel Client Setup for Application Use (e.g., Metrics) ---
SENTINEL_HOSTS_STR = os.getenv('REDIS_SENTINEL_HOSTS')
MASTER_NAME = os.getenv('REDIS_PRIMARY_NAME', 'redis-primary')
REDIS_DB = int(os.getenv('REDIS_DATABASE', 0))

SENTINEL_HOSTS = []
if SENTINEL_HOSTS_STR:
    for pair in SENTINEL_HOSTS_STR.split(','):
        host, port = pair.split(':')
        SENTINEL_HOSTS.append((host, int(port)))

_sentinel = None
_redis_client = None

@lru_cache(maxsize=1)
def get_redis_client():
    """
    Initializes and returns the Redis master client via Sentinel.
    Uses lru_cache to ensure the connection is only established once.
    """
    global _sentinel, _redis_client
    if _redis_client is None:
        print(f"Connecting to Redis Sentinel at: {SENTINEL_HOSTS}")
        try:
            _sentinel = Sentinel(SENTINEL_HOSTS,
                                 socket_timeout=1,
                                 socket_connect_timeout=1,
                                 retry_on_timeout=True)
            _redis_client = _sentinel.master_for(MASTER_NAME, db=REDIS_DB)
            # Test connection
            _redis_client.ping()
            print("Successfully connected to Redis master.")
        except Exception as e:
            print(f"Error connecting to Redis Sentinel: {e}")
            # In a critical failure scenario, raise the error or use a fallback
            raise ConnectionError(f"Could not connect to Redis: {e}")

    return _redis_client


CELERY_DEFAULT_QUEUE = os.getenv("CELERY_DEFAULT_QUEUE", "celery")
CELERY_QUEUE_LENGTH = Gauge(
    'celery_queue_length_total',
    'Current number of tasks in the Celery default queue.',
    ['queue_name']  # Using a label in case you want to monitor multiple queues
)


# preload openapi doc
def load_openapi():
    p = Path(app.root_path) / 'static' / 'openapi.yml'
    if p.exists():
        with open(p) as fh:
            return yaml.safe_load(fh)
    else:
        return {}


OPENAPI = load_openapi()


# Define routes for subscription manager
# GET list of subscriptions
@app.route('/subscriptions')
def list_subscriptions():
    subscriptions = {}
    for subscriber, item in SUBSCRIBERS.items():
        subscriptions[subscriber] = item.active_subscriptions
    return jsonify(subscriptions)


# POST (add) new subscription
@app.post('/subscriptions')
def add_subscription():
    # First parse the request query
    data = get_json()
    # Get location (target) where we want to save the data for this topic
    target = normalise_path(data.get('target', ''))
    LOGGER.error(target)

    # Next we need to normalise the topic,
    topic = normalise_topic(data.get('topic'))
    # Now check  we have topic
    if topic is None:
        return jsonify({"error": "No topic provided"}), 400

    # Now iterate over subscribers and add new subscription
    # Todo - check we are now already subscribed.
    subscriptions = {}
    for subscriber, item in SUBSCRIBERS.items():
        subscriptions[subscriber] = item.subscribe(topic, target)

    # Now update config settings and save
    CONFIG.setdefault('topics', {})[topic] = target
    persist_config(CONFIG)

    # Now create response
    response = jsonify(subscriptions)
    response.status_code = 201
    response.headers['Location'] = url_for('get_subscription', topic=topic)
    return response


# GET information on subscription
@app.get('/subscriptions/<path:topic>')
def get_subscription(topic):
    topic = unquote(topic)
    if not topic:
        return "No topic passed"
    subscriptions = {}
    for broker, item in SUBSCRIBERS.items():
        subscriptions[broker] = item.active_subscriptions[topic]
    return jsonify(subscriptions)


# DELETE subscription
@app.delete('/subscriptions/<path:topic>')
def delete_subscription(topic):
    topic = unquote(topic)
    if not topic:
        return "No topic passed"
    if topic not in CONFIG['topics']:
        LOGGER.warning(
            f"topic {topic} not found, trying to unsubscribe anyway")

    subscriptions = {}
    for broker, item in SUBSCRIBERS.items():
        subscriptions[broker] = item.unsubscribe(topic)
    LOGGER.info(f"Removing {topic}")
    LOGGER.info(json.dumps(CONFIG, indent=4))
    if topic in CONFIG['topics']:
        del CONFIG['topics'][topic]
    persist_config(CONFIG)
    return Response(response=json.dumps(subscriptions), status=200,
                    mimetype="application/json")


# Swagger end point
@app.route('/')
@app.route('/swagger')
def render_swagger():
    return render_template('swagger.html', )


# Openapi doc endpoint
@app.route('/openapi')
def fetch_openapi():
    return jsonify(OPENAPI)


@app.route('/metrics')
def expose_metrics():
    """
    Expose the Prometheus metrics to be scraped.
    """

    redis_client = get_redis_client()
    try:
        # Use the Sentinel-aware redis_client to check queue length
        queue_length = redis_client.llen(CELERY_DEFAULT_QUEUE)
        CELERY_QUEUE_LENGTH.labels(queue_name=CELERY_DEFAULT_QUEUE).set(
            queue_length)
        registry = CollectorRegistry()
        basedir = os.getenv('PROMETHEUS_MULTIPROC_DIR',
                            '/tmp/prometheus_metrics')
        multiprocess.MultiProcessCollector(registry, path=basedir)

        # ToDo fix aggregation below

        # iterate over subdirectories
        for subdir in os.listdir(basedir):
            if os.path.isdir(os.path.join(basedir, subdir)):
                worker_path = os.path.join(basedir, subdir)
                multiprocess.MultiProcessCollector(registry, path=worker_path)

        return Response(generate_latest(registry), mimetype="text/plain")

    except Exception as e:
        LOGGER.error(
            f"Failed to generate metrics: {e}. Check Sentinel connection.")
        error_message = "Error generating metrics"
        return Response(error_message, status=500, mimetype="text/plain")


# health check end point
@app.route('/health')
def health_check():
    # Health check that pings the Sentinel-aware Redis client
    try:
        redis_client.ping()
        status = 'healthy'
    except Exception as e:
        LOGGER.error(f"Redis Sentinel connection failed for health check: {e}")
        status = 'unhealthy'

    return Response(response=json.dumps({'status': status}), status=200,
                    mimetype="application/json")


def run():
    app.run(debug=True, host=CONFIG['flask_host'],
            port=CONFIG['flask_port'], use_reloader=False)
    shutdown()
