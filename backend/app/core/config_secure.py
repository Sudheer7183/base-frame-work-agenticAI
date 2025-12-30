"""
Enhanced Configuration with Secrets Management

This replaces hardcoded credentials with secure secrets management.
Place this as: backend/app/core/config_secure.py

After testing, replace the original config.py with this version.
"""

from typing import List, Optional
from functools import lru_cache
import json
import logging

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Import secrets manager
from app.core.secrets import get_secrets_manager

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with secure secrets management."""

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    APP_NAME: str = "agentic-ai-platform"
    APP_VERSION: str = "1.2.0"
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    DEBUG: bool = False
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    API_HOST: str = "0.0.0.0"
    API_PORT: int = Field(default=8000, ge=1024, le=65535)
    API_PREFIX: str = "/api/v1"
    API_WORKERS: int = Field(default=4, ge=1, le=32)

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173", "http://localhost:8501"]
    )
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH"]
    )
    CORS_HEADERS: List[str] = Field(default_factory=lambda: ["*"])

    # ------------------------------------------------------------------
    # Rate Limiting
    # ------------------------------------------------------------------
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, ge=1)

    # ------------------------------------------------------------------
    # Database - Using Secrets Manager
    # ------------------------------------------------------------------
    DB_HOST: str = "localhost"
    DB_PORT: int = Field(default=5432, ge=1024, le=65535)
    DB_NAME: str = "agentic"
    DB_USER: str = "postgres"
    DB_PASSWORD: Optional[str] = None  # Will be loaded from secrets
    DB_URL: Optional[str] = None

    # Pooling
    DB_POOL_SIZE: int = Field(default=20, ge=5, le=100)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DB_POOL_TIMEOUT: int = Field(default=30, ge=5, le=120)
    DB_POOL_RECYCLE: int = Field(default=1800, ge=300)

    # ------------------------------------------------------------------
    # Redis - Using Secrets Manager
    # ------------------------------------------------------------------
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = Field(default=6379, ge=1024, le=65535)
    REDIS_DB: int = Field(default=0, ge=0, le=15)
    REDIS_PASSWORD: Optional[str] = None  # Will be loaded from secrets
    REDIS_URL: Optional[str] = None

    # ------------------------------------------------------------------
    # Keycloak - Using Secrets Manager
    # ------------------------------------------------------------------
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "agentic"
    KEYCLOAK_CLIENT_ID: str = "agentic-api"
    KEYCLOAK_CLIENT_SECRET: Optional[str] = None  # Will be loaded from secrets
    KEYCLOAK_ADMIN_USERNAME: str = "admin"
    KEYCLOAK_ADMIN_PASSWORD: Optional[str] = None  # Will be loaded from secrets

    # JWT
    JWT_ALGORITHM: str = "RS256"
    JWT_PUBLIC_KEY_URL: Optional[str] = None

    # ------------------------------------------------------------------
    # LLM Providers - Using Secrets Manager
    # ------------------------------------------------------------------
    LLM_DEFAULT_PROVIDER: str = Field(
        default="ollama",
        pattern="^(ollama|openai|anthropic)$"
    )
    
    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    OLLAMA_TIMEOUT: int = Field(default=120, ge=30, le=600)
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None  # Will be loaded from secrets
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)
    OPENAI_MAX_TOKENS: int = Field(default=2000, ge=1, le=8000)
    
    # Anthropic
    ANTHROPIC_API_KEY: Optional[str] = None  # Will be loaded from secrets
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"
    ANTHROPIC_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=1.0)
    ANTHROPIC_MAX_TOKENS: int = Field(default=2000, ge=1, le=8000)

    # ------------------------------------------------------------------
    # Security - Using Secrets Manager
    # ------------------------------------------------------------------
    SECRET_KEY: Optional[str] = None  # Will be loaded from secrets
    API_KEY_ENABLED: bool = False
    
    # Password Policy
    PASSWORD_MIN_LENGTH: int = Field(default=8, ge=8, le=128)
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True

    # Session
    SESSION_TIMEOUT_MINUTES: int = Field(default=60, ge=5, le=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=30)

    # ------------------------------------------------------------------
    # Observability
    # ------------------------------------------------------------------
    SENTRY_DSN: Optional[str] = None  # Will be loaded from secrets
    SENTRY_ENVIRONMENT: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1, ge=0.0, le=1.0)

    # OpenTelemetry
    OTEL_ENABLED: bool = False
    OTEL_SERVICE_NAME: Optional[str] = None
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"

    # ------------------------------------------------------------------
    # LangGraph
    # ------------------------------------------------------------------
    LANGGRAPH_CHECKPOINT_DB_URL: Optional[str] = None

    # ------------------------------------------------------------------
    # Email - Using Secrets Manager
    # ------------------------------------------------------------------
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = Field(default=587, ge=1, le=65535)
    SMTP_USER: Optional[str] = None  # Will be loaded from secrets
    SMTP_PASSWORD: Optional[str] = None  # Will be loaded from secrets
    SMTP_FROM_EMAIL: str = "noreply@agentic.ai"
    SMTP_FROM_NAME: str = "Agentic AI Platform"

    # ------------------------------------------------------------------
    # File Upload
    # ------------------------------------------------------------------
    UPLOAD_DIR: str = "/tmp/uploads"
    MAX_UPLOAD_SIZE_MB: int = Field(default=10, ge=1, le=100)
    ALLOWED_EXTENSIONS: List[str] = Field(
        default_factory=lambda: ["pdf", "txt", "csv", "json", "xlsx"]
    )

    # ------------------------------------------------------------------
    # Feature Flags
    # ------------------------------------------------------------------
    FEATURE_AGENT_EXECUTION: bool = True
    FEATURE_HITL: bool = True
    FEATURE_MULTI_TENANCY: bool = False
    FEATURE_AUDIT_LOG: bool = True
    FEATURE_ADVANCED_ANALYTICS: bool = False

    # ------------------------------------------------------------------
    # Secrets Management Configuration
    # ------------------------------------------------------------------
    SECRETS_PROVIDER: str = Field(
        default="local",
        pattern="^(local|vault|aws)$"
    )
    SECRETS_CACHE_TTL: int = Field(default=300, ge=60, le=3600)
    SECRETS_MASTER_KEY: Optional[str] = None
    
    # Vault Configuration
    VAULT_ADDR: Optional[str] = None
    VAULT_TOKEN: Optional[str] = None
    VAULT_NAMESPACE: Optional[str] = None
    VAULT_MOUNT_POINT: str = "secret"
    
    # AWS Secrets Manager Configuration
    AWS_REGION: Optional[str] = None
    AWS_SECRETS_PREFIX: str = "agentic-ai-platform"

    # ------------------------------------------------------------------
    # Dev / Test
    # ------------------------------------------------------------------
    AUTO_RELOAD: bool = True
    TEST_DB_URL: Optional[str] = None
    TEST_KEYCLOAK_ENABLED: bool = False
    TEST_MOCK_LLM: bool = True

    # ------------------------------------------------------------------
    # Pydantic Settings Config
    # ------------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def __init__(self, **kwargs):
        """Initialize settings and load secrets"""
        super().__init__(**kwargs)
        self._load_secrets()
    
    def _load_secrets(self):
        """Load sensitive values from secrets manager"""
        try:
            secrets_manager = get_secrets_manager()
            
            # Database password
            if self.DB_PASSWORD:
            self.DB_URL = (
                f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
            logger.info(f"✓ DB_URL rebuilt with loaded password")
            if not self.DB_PASSWORD:
                self.DB_PASSWORD = secrets_manager.get_secret(
                    "database/password",
                    default="postgres",
                    required=self.is_production
                )
            
            # Redis password
            if not self.REDIS_PASSWORD and self.is_production:
                self.REDIS_PASSWORD = secrets_manager.get_secret(
                    "redis/password",
                    default=None,
                    required=False
                )
            
            # Keycloak secrets
            if not self.KEYCLOAK_CLIENT_SECRET:
                self.KEYCLOAK_CLIENT_SECRET = secrets_manager.get_secret(
                    "keycloak/client_secret",
                    default="your-client-secret-here-change-in-production",
                    required=self.is_production
                )
            
            if not self.KEYCLOAK_ADMIN_PASSWORD:
                self.KEYCLOAK_ADMIN_PASSWORD = secrets_manager.get_secret(
                    "keycloak/admin_password",
                    default="admin",
                    required=self.is_production
                )
            
            # LLM API Keys
            if not self.OPENAI_API_KEY and self.LLM_DEFAULT_PROVIDER == "openai":
                self.OPENAI_API_KEY = secrets_manager.get_secret(
                    "llm/openai_api_key",
                    default=None,
                    required=self.is_production
                )
            
            if not self.ANTHROPIC_API_KEY and self.LLM_DEFAULT_PROVIDER == "anthropic":
                self.ANTHROPIC_API_KEY = secrets_manager.get_secret(
                    "llm/anthropic_api_key",
                    default=None,
                    required=self.is_production
                )
            
            # Application secret key
            if not self.SECRET_KEY:
                self.SECRET_KEY = secrets_manager.get_secret(
                    "application/secret_key",
                    default="dev-secret-key-change-in-production",
                    required=self.is_production
                )
            
            # Email credentials
            if not self.SMTP_USER and self.is_production:
                self.SMTP_USER = secrets_manager.get_secret(
                    "email/smtp_user",
                    default=None,
                    required=False
                )
            
            if not self.SMTP_PASSWORD and self.is_production:
                self.SMTP_PASSWORD = secrets_manager.get_secret(
                    "email/smtp_password",
                    default=None,
                    required=False
                )
            
            # Sentry DSN
            if not self.SENTRY_DSN and self.is_production:
                self.SENTRY_DSN = secrets_manager.get_secret(
                    "observability/sentry_dsn",
                    default=None,
                    required=False
                )
            
            logger.info(f"Loaded secrets for {self.ENVIRONMENT} environment")
            
        except Exception as e:
            logger.error(f"Error loading secrets: {e}")
            if self.is_production:
                raise RuntimeError(f"Failed to load required secrets: {e}")

    # ------------------------------------------------------------------
    # Validators (same as before)
    # ------------------------------------------------------------------
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("DB_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v, info):
        if v:
            return v
        d = info.data
        password = d.get('DB_PASSWORD', 'postgres')
        return (
            f"postgresql://{d['DB_USER']}:{password}"
            f"@{d['DB_HOST']}:{d['DB_PORT']}/{d['DB_NAME']}"
        )

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_url(cls, v, info):
        if v:
            return v
        d = info.data
        auth = f":{d['REDIS_PASSWORD']}@" if d.get("REDIS_PASSWORD") else ""
        return f"redis://{auth}{d['REDIS_HOST']}:{d['REDIS_PORT']}/{d['REDIS_DB']}"

    @field_validator("JWT_PUBLIC_KEY_URL", mode="before")
    @classmethod
    def assemble_jwt_url(cls, v, info):
        if v:
            return v
        d = info.data
        return f"{d['KEYCLOAK_URL']}/realms/{d['KEYCLOAK_REALM']}/protocol/openid-connect/certs"

    @field_validator("LANGGRAPH_CHECKPOINT_DB_URL", mode="before")
    @classmethod
    def assemble_langgraph_url(cls, v, info):
        return v or info.data.get("DB_URL")

    @field_validator("SENTRY_ENVIRONMENT", mode="before")
    @classmethod
    def set_sentry_environment(cls, v, info):
        return v or info.data.get("ENVIRONMENT", "development")

    @field_validator("OTEL_SERVICE_NAME", mode="before")
    @classmethod
    def set_otel_service_name(cls, v, info):
        return v or info.data.get("APP_NAME")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def database_url_async(self) -> str:
        return self.DB_URL.replace("postgresql://", "postgresql+asyncpg://")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()