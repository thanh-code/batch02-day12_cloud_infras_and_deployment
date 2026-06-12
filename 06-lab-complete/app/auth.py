"""API key authentication for the production agent."""
import hashlib
import hmac

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

from .config import settings


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _user_id_from_api_key(api_key: str) -> str:
    digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()[:16]
    return f"api-key:{digest}"


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Validate X-API-Key and return a stable user id for quotas/history."""
    if not api_key or not hmac.compare_digest(api_key, settings.agent_api_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Include header: X-API-Key: <key>",
        )
    return _user_id_from_api_key(api_key)
