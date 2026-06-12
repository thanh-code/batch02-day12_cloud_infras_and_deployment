"""Production config: 12-factor settings loaded from environment variables."""
import os
import logging
from dataclasses import dataclass, field


def _bool_env(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: str) -> int:
    return int(os.getenv(name, default))


def _float_env(name: str, default: str) -> float:
    return float(os.getenv(name, default))


def _csv_env(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default).strip()
    if raw == "*":
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


def _redis_url_env() -> str:
    explicit = os.getenv("REDIS_URL", "").strip()
    if explicit:
        return explicit

    host = os.getenv("REDIS_HOST", "").strip()
    if not host:
        return ""

    port = os.getenv("REDIS_PORT", "6379").strip()
    db = os.getenv("REDIS_DB", "0").strip()
    return f"redis://{host}:{port}/{db}"


@dataclass
class Settings:
    # Server
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _int_env("PORT", "8000"))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: _bool_env("DEBUG"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    instance_id: str = field(default_factory=lambda: os.getenv("INSTANCE_ID", os.uname().nodename))

    # App
    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "Production AI Agent"))
    app_version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"))

    # LLM
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))

    # Security
    agent_api_key: str = field(default_factory=lambda: os.getenv("AGENT_API_KEY", "dev-key-change-me"))
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", "dev-jwt-secret"))
    allowed_origins: list[str] = field(default_factory=lambda: _csv_env("ALLOWED_ORIGINS", "*"))

    # Rate limiting
    rate_limit_per_minute: int = field(
        default_factory=lambda: _int_env("RATE_LIMIT_PER_MINUTE", "10")
    )
    rate_limit_window_seconds: int = field(
        default_factory=lambda: _int_env("RATE_LIMIT_WINDOW_SECONDS", "60")
    )

    # Budget
    monthly_budget_usd: float = field(
        default_factory=lambda: _float_env(
            "MONTHLY_BUDGET_USD", os.getenv("DAILY_BUDGET_USD", "10.0")
        )
    )
    estimated_output_tokens: int = field(
        default_factory=lambda: _int_env("ESTIMATED_OUTPUT_TOKENS", "300")
    )

    # Redis-backed state
    redis_url: str = field(default_factory=_redis_url_env)
    history_ttl_seconds: int = field(
        default_factory=lambda: _int_env("HISTORY_TTL_SECONDS", str(30 * 24 * 3600))
    )
    max_history_messages: int = field(
        default_factory=lambda: _int_env("MAX_HISTORY_MESSAGES", "20")
    )

    def validate(self):
        logger = logging.getLogger(__name__)
        env = self.environment.lower()
        if self.environment == "production":
            weak_api_keys = {"dev-key-change-me", "dev-key-change-me-in-production"}
            weak_jwt_secrets = {"dev-jwt-secret", "dev-jwt-secret-change-in-production"}
            if self.agent_api_key in weak_api_keys:
                raise ValueError("AGENT_API_KEY must be set in production!")
            if self.jwt_secret in weak_jwt_secrets:
                raise ValueError("JWT_SECRET must be set in production!")
            if not self.redis_url:
                raise ValueError("REDIS_URL must be set in production for stateless storage!")
        if self.rate_limit_per_minute <= 0:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be greater than 0")
        if self.monthly_budget_usd <= 0:
            raise ValueError("MONTHLY_BUDGET_USD must be greater than 0")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not set; using mock LLM")
        if env not in {"development", "staging", "production", "test"}:
            logger.warning("Unknown ENVIRONMENT=%s", self.environment)
        return self


settings = Settings().validate()
