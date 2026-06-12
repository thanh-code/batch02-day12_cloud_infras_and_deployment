"""Monthly per-user budget guard backed by Redis."""
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from redis.exceptions import RedisError

from .config import settings
from .storage import get_redis


PRICE_PER_1K_INPUT_TOKENS = 0.00015
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006

_memory_usage: dict[str, dict[str, Any]] = defaultdict(
    lambda: {
        "cost_usd": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
        "request_count": 0,
    }
)


def estimate_tokens(text: str) -> int:
    """Small deterministic estimate for mock/demo LLM calls."""
    return max(1, len(text.split()) * 2)


def estimate_cost_usd(input_tokens: int = 0, output_tokens: int = 0) -> float:
    input_cost = (input_tokens / 1000) * PRICE_PER_1K_INPUT_TOKENS
    output_cost = (output_tokens / 1000) * PRICE_PER_1K_OUTPUT_TOKENS
    return round(input_cost + output_cost, 8)


def _month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _budget_key(user_id: str) -> str:
    return f"budget:{user_id}:{_month()}"


def _ttl_seconds() -> int:
    return 32 * 24 * 3600


def _normalize_usage(data: dict[str, Any], user_id: str, storage: str) -> dict[str, Any]:
    cost = float(data.get("cost_usd") or 0)
    request_count = int(data.get("request_count") or 0)
    input_tokens = int(data.get("input_tokens") or 0)
    output_tokens = int(data.get("output_tokens") or 0)
    budget = settings.monthly_budget_usd
    return {
        "user_id": user_id,
        "month": _month(),
        "requests": request_count,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost, 6),
        "budget_usd": budget,
        "remaining_usd": round(max(0.0, budget - cost), 6),
        "budget_used_pct": round((cost / budget) * 100, 2),
        "storage": storage,
    }


def get_usage(user_id: str) -> dict[str, Any]:
    client = get_redis()
    if client is not None:
        try:
            return _normalize_usage(client.hgetall(_budget_key(user_id)), user_id, "redis")
        except RedisError:
            if settings.environment.lower() == "production":
                raise HTTPException(status_code=503, detail="Budget store unavailable")
    return _normalize_usage(_memory_usage[user_id], user_id, "memory")


def check_budget(user_id: str, estimated_cost: float = 0.0) -> dict[str, Any]:
    usage = get_usage(user_id)
    projected = usage["cost_usd"] + estimated_cost
    if projected > settings.monthly_budget_usd:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Monthly budget exceeded",
                "used_usd": usage["cost_usd"],
                "estimated_request_cost_usd": round(estimated_cost, 6),
                "budget_usd": settings.monthly_budget_usd,
                "resets": "first day of next UTC month",
            },
        )
    return usage


def record_usage(user_id: str, input_tokens: int, output_tokens: int) -> dict[str, Any]:
    cost = estimate_cost_usd(input_tokens, output_tokens)
    client = get_redis()

    if client is not None:
        try:
            key = _budget_key(user_id)
            pipe = client.pipeline()
            pipe.hincrbyfloat(key, "cost_usd", cost)
            pipe.hincrby(key, "input_tokens", input_tokens)
            pipe.hincrby(key, "output_tokens", output_tokens)
            pipe.hincrby(key, "request_count", 1)
            pipe.expire(key, _ttl_seconds())
            pipe.execute()
            return get_usage(user_id)
        except RedisError as exc:
            if settings.environment.lower() == "production":
                raise HTTPException(status_code=503, detail="Budget store unavailable") from exc

    usage = _memory_usage[user_id]
    usage["cost_usd"] = float(usage["cost_usd"]) + cost
    usage["input_tokens"] = int(usage["input_tokens"]) + input_tokens
    usage["output_tokens"] = int(usage["output_tokens"]) + output_tokens
    usage["request_count"] = int(usage["request_count"]) + 1
    return get_usage(user_id)
