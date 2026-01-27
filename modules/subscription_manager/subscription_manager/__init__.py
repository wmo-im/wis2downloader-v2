__version__ = "v0.2.0"
from flask import request
import json
import logging
import os
import threading
from urllib.parse import unquote
from uuid import uuid4
from .subscriber import Subscriber

# Setup defaults for the subscription manager package
DEFAULT_FLASK_HOST = "0.0.0.0"
DEFAULT_FLASK_PORT = 5001
DEFAULT_BROKER_HOST = "globalbroker.meteo.fr"
DEFAULT_BROKER_PORT = 443
DEFAULT_USERNAME = "everyone"
DEFAULT_PASSWORD = "everyone"
DEFAULT_PROTOCOL = "websockets"

# get logger
LOGGER = logging.getLogger(__name__)

# global lock to protect the config file
CONFIG_FILE_LOCK = threading.Lock()
# Now get the config file path
CONFIG_PATH = os.getenv("CONFIG_PATH", "/app/config/config.json")

def load_config() -> dict:
    CONFIG_FILE_LOCK.acquire()
    try:
        if not os.path.exists(CONFIG_PATH):
            LOGGER.warning(f"Config file {CONFIG_PATH} not found, using defaults")
            return {"brokers": {}, "topics": {}, "flask_host": DEFAULT_FLASK_HOST,
                    "flask_port": DEFAULT_FLASK_PORT}
        with open(CONFIG_PATH) as fh:
            try:
                _config = json.load(fh)
                _config.setdefault('brokers',{})
                _config.setdefault('topics',{})
                _config.setdefault('flask_host', DEFAULT_FLASK_HOST)
                _config.setdefault('flask_port', DEFAULT_FLASK_PORT)
                return _config
            except json.JSONDecodeError as e:
                LOGGER.error(f"Failed to load configuration file: {e}")
                return {"brokers": {}, "topics": {}, "flask_host": DEFAULT_FLASK_HOST,
                    "flask_port": DEFAULT_FLASK_PORT}
    finally:
        CONFIG_FILE_LOCK.release()


def save_config(config: dict) -> None:
    CONFIG_FILE_LOCK.acquire()
    _temp_file = CONFIG_PATH + ".temp"

    try:
        with open(_temp_file, 'w') as fh:
            fh.write(json.dumps(config, indent=4))
        os.replace(_temp_file, CONFIG_PATH)
    except Exception as e:
        LOGGER.error(f"Failed to save configuration file: {e}")
        if os.path.exists(_temp_file):
            os.remove(_temp_file)
            LOGGER.debug(f"Cleaned up temporary file: {_temp_file}")
    finally:
        CONFIG_FILE_LOCK.release()


def shutdown():
    """Shutdown all subscriber threads."""
    for broker_name, _subscriber in SUBSCRIBERS.items():
        _subscriber.stop()
        thread = SUBSCRIBER_THREADS[broker_name]
        thread.join(timeout=5)
        if thread.is_alive():
            LOGGER.error(f"Failed to shutdown subscriber thread for {broker_name} gracefully")

