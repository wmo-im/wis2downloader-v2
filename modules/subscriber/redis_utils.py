from functools import lru_cache
import os
import redis
from redis.sentinel import Sentinel

LOGGER = logging.getLogger(__name__)
LOG_LEVEL = os.getenv("LOG_LEVEL","DEBUG").upper()
LOGGER.setLevel(LOG_LEVEL)

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