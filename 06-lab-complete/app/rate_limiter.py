"""Redis-backed sliding-window rate limiting."""
import time
import uuid
from collections import defaultdict, deque
from typing import Any

from fastapi import HTTPException
from redis.exceptions import RedisError

from .config import settings
from .storage import get_redis


_memory_windows: dict[str, deque[float]] = defaultdict(deque)


def _rate_limit_headers(limit: int, remaining: int, reset_at: int, retry_after: int | None = None) -> dict[str, str]:
    headers = {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(max(0, remaining)),
        "X-RateLimit-Reset": str(reset_at),
    }
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    return headers


def _raise_limit_exceeded(retry_after: int, reset_at: int) -> None:
    raise HTTPException(
        status_code=429,
        detail={
            "error": "Rate limit exceeded",
            "limit": settings.rate_limit_per_minute,
            "window_seconds": settings.rate_limit_window_seconds,
            "retry_after_seconds": retry_after,
        },
        headers=_rate_limit_headers(
            settings.rate_limit_per_minute,
            0,
            reset_at,
            retry_after,
        ),
    )


def _check_memory(user_id: str) -> dict[str, Any]:
    now = time.time()
    window = _memory_windows[user_id]
    window_start = now - settings.rate_limit_window_seconds

    while window and window[0] < window_start:
        window.popleft()

    if len(window) >= settings.rate_limit_per_minute:
        retry_after = max(1, int(window[0] + settings.rate_limit_window_seconds - now) + 1)
        reset_at = int(window[0] + settings.rate_limit_window_seconds)
        _raise_limit_exceeded(retry_after, reset_at)

    window.append(now)
    remaining = settings.rate_limit_per_minute - len(window)
    reset_at = int(now + settings.rate_limit_window_seconds)
    return {
        "limit": settings.rate_limit_per_minute,
        "remaining": remaining,
        "reset_at": reset_at,
        "storage": "memory",
    }


def _check_redis(user_id: str) -> dict[str, Any]:
    client = get_redis()
    if client is None:
        raise RedisError("REDIS_URL is not configured")

    now_ms = int(time.time() * 1000)
    window_ms = settings.rate_limit_window_seconds * 1000
    window_start_ms = now_ms - window_ms
    key = f"rate:{user_id}"

    pipe = client.pipeline()
    pipe.zremrangebyscore(key, 0, window_start_ms)
    pipe.zcard(key)
    _, current_count = pipe.execute()

    if current_count >= settings.rate_limit_per_minute:
        oldest = client.zrange(key, 0, 0, withscores=True)
        oldest_score = int(oldest[0][1]) if oldest else now_ms
        retry_after = max(1, int((oldest_score + window_ms - now_ms) / 1000) + 1)
        reset_at = int((oldest_score + window_ms) / 1000)
        _raise_limit_exceeded(retry_after, reset_at)

    member = f"{now_ms}:{uuid.uuid4().hex}"
    pipe = client.pipeline()
    pipe.zadd(key, {member: now_ms})
    pipe.expire(key, settings.rate_limit_window_seconds * 2)
    pipe.execute()

    remaining = settings.rate_limit_per_minute - current_count - 1
    reset_at = int((now_ms + window_ms) / 1000)
    return {
        "limit": settings.rate_limit_per_minute,
        "remaining": remaining,
        "reset_at": reset_at,
        "storage": "redis",
    }


def check_rate_limit(user_id: str) -> dict[str, Any]:
    """Record this request and raise 429 if the user is over quota."""
    try:
        return _check_redis(user_id)
    except RedisError as exc:
        if settings.environment.lower() == "production":
            raise HTTPException(status_code=503, detail="Rate limiter unavailable") from exc
        return _check_memory(user_id)
