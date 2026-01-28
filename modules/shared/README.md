# Shared Module

Common utilities used across all WIS2 Downloader services.

## Overview

This module provides:
- Sentinel-aware Redis client with automatic failover
- Centralized logging configuration with UTC timestamps

## Documentation

- [Developer Guide](../../docs/developer-guide.adoc) - Architecture and code details

## Usage

```python
from shared import get_redis_client, setup_logging

# Configure root logger (call once at startup)
setup_logging()

# Get module-specific logger
LOGGER = setup_logging(__name__)

# Get Redis client (singleton, Sentinel-aware)
redis = get_redis_client()
redis.set('key', 'value')
```

## Key Files

| File | Description |
|------|-------------|
| `redis_client.py` | Sentinel-aware Redis client singleton |
| `logging.py` | Centralized logging with UTC timestamps |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_SENTINEL_HOSTS` | - | Comma-separated sentinel hosts (host:port) |
| `REDIS_PRIMARY_NAME` | `redis-primary` | Sentinel master name |
| `REDIS_DATABASE` | `0` | Redis database number |
| `REDIS_HOST` | `localhost` | Direct Redis host (fallback) |
| `REDIS_PORT` | `6379` | Direct Redis port (fallback) |
| `LOG_LEVEL` | `DEBUG` | Logging level |
