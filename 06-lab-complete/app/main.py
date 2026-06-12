"""
Production AI Agent - Day 12 final lab.

Combines:
  - 12-factor environment config
  - JSON structured logging
  - API key authentication
  - Redis-backed rate limiting
  - Redis-backed monthly cost guard
  - Redis-backed conversation history
  - Health/readiness probes
  - Graceful shutdown hooks
"""
import json
import logging
import signal
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from redis.exceptions import RedisError
import uvicorn

from .auth import verify_api_key
from .config import settings
from .cost_guard import (
    check_budget,
    estimate_cost_usd,
    estimate_tokens,
    get_usage,
    record_usage,
)
from .mock_llm import ask as llm_ask
from .rate_limiter import check_rate_limit
from .storage import get_redis, redis_ping


START_TIME = time.time()
_is_ready = False
_shutdown_requested = False
_request_count = 0
_error_count = 0
_memory_history: dict[str, list[dict[str, str]]] = {}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
        }

        message = record.getMessage()
        try:
            parsed = json.loads(message)
        except json.JSONDecodeError:
            payload["message"] = message
        else:
            if isinstance(parsed, dict):
                payload.update(parsed)
            else:
                payload["message"] = message

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.DEBUG if settings.debug else settings.log_level.upper())


configure_logging()
logger = logging.getLogger(__name__)


def _storage_name() -> str:
    return "redis" if settings.redis_url and redis_ping() else "memory"


def _history_key(user_id: str, session_id: str) -> str:
    return f"history:{user_id}:{session_id}"


def load_history(user_id: str, session_id: str) -> list[dict[str, str]]:
    key = _history_key(user_id, session_id)
    client = get_redis()
    if client is not None:
        try:
            raw_messages = client.lrange(key, 0, -1)
            messages: list[dict[str, str]] = []
            for raw in raw_messages:
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict):
                        messages.append(parsed)
                except json.JSONDecodeError:
                    logger.warning(json.dumps({"event": "history_decode_failed", "session_id": session_id}))
            return messages
        except RedisError as exc:
            if settings.environment.lower() == "production":
                raise HTTPException(status_code=503, detail="Conversation store unavailable") from exc

    return list(_memory_history.get(key, []))


def append_history(user_id: str, session_id: str, role: str, content: str) -> list[dict[str, str]]:
    key = _history_key(user_id, session_id)
    entry = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    client = get_redis()
    if client is not None:
        try:
            pipe = client.pipeline()
            pipe.rpush(key, json.dumps(entry, ensure_ascii=False))
            pipe.ltrim(key, -settings.max_history_messages, -1)
            pipe.expire(key, settings.history_ttl_seconds)
            pipe.execute()
            return load_history(user_id, session_id)
        except RedisError as exc:
            if settings.environment.lower() == "production":
                raise HTTPException(status_code=503, detail="Conversation store unavailable") from exc

    history = _memory_history.setdefault(key, [])
    history.append(entry)
    if len(history) > settings.max_history_messages:
        del history[:-settings.max_history_messages]
    return list(history)


def delete_history(user_id: str, session_id: str) -> None:
    key = _history_key(user_id, session_id)
    client = get_redis()
    if client is not None:
        try:
            client.delete(key)
            return
        except RedisError as exc:
            if settings.environment.lower() == "production":
                raise HTTPException(status_code=503, detail="Conversation store unavailable") from exc
    _memory_history.pop(key, None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "instance_id": settings.instance_id,
        "selected_cloud": "render",
    }))

    if settings.redis_url and not redis_ping():
        logger.warning(json.dumps({"event": "redis_unavailable_at_startup"}))

    _is_ready = True
    logger.info(json.dumps({"event": "ready", "storage": _storage_name()}))

    yield

    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment.lower() != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count, _error_count

    if _shutdown_requested and request.url.path not in {"/health", "/ready"}:
        return JSONResponse(
            status_code=503,
            content={"detail": "Server is shutting down"},
            headers={"Retry-After": "30"},
        )

    start = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
        if response.status_code >= 500:
            _error_count += 1

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers.pop("server", None)

        logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round((time.time() - start) * 1000, 1),
            "client": request.client.host if request.client else "unknown",
        }))
        return response
    except Exception:
        _error_count += 1
        logger.exception(json.dumps({
            "event": "request_failed",
            "method": request.method,
            "path": request.url.path,
        }))
        raise


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, min_length=1, max_length=128)
    user_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=128,
        description="Optional client-side session label; API key still controls auth and budget.",
    )


class AskResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    model: str
    turn: int
    served_by: str
    storage: str
    rate_limit: dict[str, Any]
    usage: dict[str, Any]
    timestamp: str


@app.get("/", tags=["Info"])
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "selected_cloud": "render",
        "endpoints": {
            "ask": "POST /ask (requires X-API-Key)",
            "history": "GET /sessions/{session_id}/history (requires X-API-Key)",
            "health": "GET /health",
            "ready": "GET /ready",
            "metrics": "GET /metrics (requires X-API-Key)",
        },
    }


@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(
    body: AskRequest,
    request: Request,
    user_id: str = Depends(verify_api_key),
):
    """Ask the agent a question and persist the conversation outside process memory."""
    rate_limit = check_rate_limit(user_id)

    input_tokens = estimate_tokens(body.question)
    projected_cost = estimate_cost_usd(input_tokens, settings.estimated_output_tokens)
    check_budget(user_id, projected_cost)

    session_id = body.session_id or body.user_id or str(uuid.uuid4())
    history_before = load_history(user_id, session_id)
    append_history(user_id, session_id, "user", body.question)

    logger.info(json.dumps({
        "event": "agent_call",
        "session_id": session_id,
        "history_messages": len(history_before),
        "question_length": len(body.question),
        "client": request.client.host if request.client else "unknown",
    }))

    answer = llm_ask(body.question)
    output_tokens = estimate_tokens(answer)
    usage = record_usage(user_id, input_tokens, output_tokens)
    history_after = append_history(user_id, session_id, "assistant", answer)
    turn = len([message for message in history_after if message.get("role") == "user"])

    return AskResponse(
        session_id=session_id,
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        turn=turn,
        served_by=settings.instance_id,
        storage=_storage_name(),
        rate_limit=rate_limit,
        usage=usage,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/sessions/{session_id}/history", tags=["Agent"])
def get_session_history(session_id: str, user_id: str = Depends(verify_api_key)):
    history = load_history(user_id, session_id)
    if not history:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "messages": history,
        "count": len(history),
        "storage": _storage_name(),
    }


@app.delete("/sessions/{session_id}", tags=["Agent"])
def delete_session(session_id: str, user_id: str = Depends(verify_api_key)):
    delete_history(user_id, session_id)
    return {"deleted": session_id}


@app.get("/health", tags=["Operations"])
def health():
    redis_ok = redis_ping() if settings.redis_url else False
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "selected_cloud": "render",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "checks": {
            "llm": "mock" if not settings.openai_api_key else settings.llm_model,
            "redis": "ok" if redis_ok else "not_configured" if not settings.redis_url else "unavailable",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Operations"])
def ready():
    if not _is_ready or _shutdown_requested:
        raise HTTPException(status_code=503, detail="Not ready")

    if settings.redis_url and not redis_ping():
        raise HTTPException(status_code=503, detail="Redis not available")

    if settings.environment.lower() == "production" and not settings.redis_url:
        raise HTTPException(status_code=503, detail="Redis is required in production")

    return {
        "ready": True,
        "instance_id": settings.instance_id,
        "storage": _storage_name(),
    }


@app.get("/metrics", tags=["Operations"])
def metrics(user_id: str = Depends(verify_api_key)):
    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "error_count": _error_count,
        "instance_id": settings.instance_id,
        "storage": _storage_name(),
        "usage": get_usage(user_id),
    }


def _handle_signal(signum, _frame):
    global _is_ready, _shutdown_requested
    _shutdown_requested = True
    _is_ready = False
    logger.info(json.dumps({"event": "signal", "signum": signum, "action": "drain"}))


signal.signal(signal.SIGTERM, _handle_signal)


if __name__ == "__main__":
    logger.info(json.dumps({
        "event": "server_start",
        "host": settings.host,
        "port": settings.port,
    }))
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
