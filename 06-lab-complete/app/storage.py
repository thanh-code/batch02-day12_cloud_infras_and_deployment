"""Redis connection helpers used by stateless production modules."""
import logging
from functools import lru_cache

import redis
from redis import Redis
from redis.exceptions import RedisError

from .config import settings


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_redis() -> Redis | None:
    """Return a cached Redis client, or None when Redis is not configured."""
    if not settings.redis_url:
        return None
    return redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
    )


def redis_ping() -> bool:
    """Check whether Redis is reachable."""
    client = get_redis()
    if client is None:
        return False
    try:
        return bool(client.ping())
    except RedisError as exc:
        logger.warning("Redis ping failed: %s", exc)
        return False


def redis_required_error(feature: str) -> RuntimeError:
    return RuntimeError(f"Redis is required for {feature} in production")
