


"""
Enhanced Configuration with Secrets Management

This configuration uses the secrets manager to load sensitive credentials
instead of hardcoding them in the source code.
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
    APP_VERSION: str = "1.3.0"
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
    DB_PORT: int = Field(default=5433, ge=1024, le=65535)
    DB_NAME: str = "agenticbase2"
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
    REDIS_PORT: int = Field(default=6379, ge=1, le=65535)
    REDIS_DB: int = Field(default=0, ge=0, le=15)
    REDIS_PASSWORD: Optional[str] = None  # Will be loaded from secrets
    REDIS_URL: Optional[str] = None

    # Cache
    CACHE_DEFAULT_TTL: int = Field(default=300, ge=60)

    # ------------------------------------------------------------------
    # Keycloak - Using Secrets Manager
    # ------------------------------------------------------------------
    KEYCLOAK_URL: str = "http://localhost:8080"
    KEYCLOAK_REALM: str = "agentic"
    KEYCLOAK_CLIENT_ID: str = "agentic-api"
    KEYCLOAK_CLIENT_SECRET: Optional[str] = "12345"  # Will be loaded from secrets
    KEYCLOAK_ADMIN_USERNAME: str = "admin"
    KEYCLOAK_ADMIN_PASSWORD: Optional[str] = None  # Will be loaded from secrets

    # ------------------------------------------------------------------
    # LLM Providers - Using Secrets Manager
    # ------------------------------------------------------------------
    LLM_DEFAULT_PROVIDER: str = "openai"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OPENAI_API_KEY: Optional[str] = "******"  # Will be loaded from secrets
    ANTHROPIC_API_KEY: Optional[str] = None  # Will be loaded from secrets
    OPENAI_BASE_URL: Optional[str]="https://api.groq.com/openai/v1"
    OPENAI_MODEL: Optional[str]="openai/gpt-oss-120b"

    # ------------------------------------------------------------------
    # Security - Using Secrets Manager
    # ------------------------------------------------------------------
    SECRET_KEY: Optional[str] = None  # Will be loaded from secrets
    JWT_SECRET_KEY: Optional[str] = None  # Will be loaded from secrets
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=5, le=1440)

    # ------------------------------------------------------------------
    # Email - Using Secrets Manager
    # ------------------------------------------------------------------
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = Field(default=587, ge=1, le=65535)
    SMTP_USER: Optional[str] = None  # Will be loaded from secrets
    SMTP_PASSWORD: Optional[str] = None  # Will be loaded from secrets
    EMAIL_FROM: str = "noreply@agenticai.com"

    # ------------------------------------------------------------------
    # Monitoring
    # ------------------------------------------------------------------
    METRICS_ENABLED: bool = True
    OTEL_ENABLED: bool = False
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
    SENTRY_DSN: Optional[str] = None

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

    #---------------------------------------------------------------------
    #Backup settings
    #---------------------------------------------------------------------

    BACKUP_ENABLED: bool = Field(default=True)
    BACKUP_DIR: str = Field(default="/backups")
    BACKUP_RETENTION_DAYS: int = Field(default=30, ge=1)
    BACKUP_MAX_COUNT: int = Field(default=50, ge=1)
    
    # Backup Schedule
    BACKUP_FULL_SCHEDULE: str = Field(default="0 2 * * *")  # Daily at 2 AM
    BACKUP_TENANT_INTERVAL_HOURS: int = Field(default=12, ge=1)
    
    # Backup Monitoring
    BACKUP_MONITORING_ENABLED: bool = Field(default=True)
    BACKUP_ALERT_EMAIL: Optional[str] = None
    
    # Backup Storage
    BACKUP_COMPRESSION: bool = Field(default=True)
    BACKUP_AUTO_VERIFY: bool = Field(default=True)
    #--------------------------------------------------------------------------

    def __init__(self, **kwargs):
        """Initialize settings and load secrets"""
        super().__init__(**kwargs)
        self._load_secrets()
    
    def _load_secrets(self):
        """Load sensitive values from secrets manager"""
        try:
            secrets_manager = get_secrets_manager()
            
            # Database password
            if not self.DB_PASSWORD:
                self.DB_PASSWORD = secrets_manager.get_secret(
                    "DB_PASSWORD",
                    default="postgres",
                    required=self.is_production
                )
            
            # Redis password (optional)
            if not self.REDIS_PASSWORD and self.is_production:
                self.REDIS_PASSWORD = secrets_manager.get_secret(
                    "REDIS_PASSWORD",
                    default=None,
                    required=False
                )
            
            if self.DB_PASSWORD:
                self.DB_URL = (
                    f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@"
                    f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
                )
                logger.info(f"✓ DB_URL rebuilt with password from Vault")
        
            # Rebuild Redis URL if password was loaded
            if self.REDIS_PASSWORD:
                self.REDIS_URL = (
                    f"redis://:{self.REDIS_PASSWORD}@"
                    f"{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
                )
            # Keycloak secrets
            if not self.KEYCLOAK_CLIENT_SECRET:
                self.KEYCLOAK_CLIENT_SECRET = secrets_manager.get_secret(
                    "KEYCLOAK_CLIENT_SECRET",
                    default="your-client-secret-here-change-in-production",
                    required=self.is_production
                )
            
            if not self.KEYCLOAK_ADMIN_PASSWORD:
                self.KEYCLOAK_ADMIN_PASSWORD = secrets_manager.get_secret(
                    "KEYCLOAK_ADMIN_PASSWORD",
                    default="admin123",
                    required=False
                )
            
            # Application secrets
            if not self.SECRET_KEY:
                self.SECRET_KEY = secrets_manager.get_secret(
                    "SECRET_KEY",
                    default="dev-secret-key-replace-in-production",
                    required=self.is_production
                )
            
            if not self.JWT_SECRET_KEY:
                self.JWT_SECRET_KEY = secrets_manager.get_secret(
                    "JWT_SECRET_KEY",
                    default="dev-jwt-secret-key-replace-in-production",
                    required=self.is_production
                )
            
            # LLM API keys (optional)
            if not self.OPENAI_API_KEY:
                self.OPENAI_API_KEY = secrets_manager.get_secret(
                    "OPENAI_API_KEY",
                    default=None,
                    required=False
                )
            
            if not self.ANTHROPIC_API_KEY:
                self.ANTHROPIC_API_KEY = secrets_manager.get_secret(
                    "ANTHROPIC_API_KEY",
                    default=None,
                    required=False
                )
            
            # Email credentials (optional)
            if not self.SMTP_USER:
                self.SMTP_USER = secrets_manager.get_secret(
                    "SMTP_USER",
                    default=None,
                    required=False
                )
            
            if not self.SMTP_PASSWORD:
                self.SMTP_PASSWORD = secrets_manager.get_secret(
                    "SMTP_PASSWORD",
                    default=None,
                    required=False
                )
            
            logger.info("✓ Secrets loaded successfully from secrets manager")
            
        except Exception as e:
            logger.warning(f"⚠ Failed to load some secrets: {e}")
            if self.is_production:
                raise RuntimeError(f"Secrets loading failed in production: {e}")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT == "development"
    
    def model_post_init(self, __context) -> None:
        """Build composite configuration values after initialization"""
        # Build database URL if not provided
        if not self.DB_URL:
            password = self.DB_PASSWORD or ""
            self.DB_URL = (
                f"postgresql://{self.DB_USER}:{password}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        
        # Build Redis URL if not provided
        if not self.REDIS_URL:
            if self.REDIS_PASSWORD:
                self.REDIS_URL = (
                    f"redis://:{self.REDIS_PASSWORD}@"
                    f"{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
                )
            else:
                self.REDIS_URL = (
                    f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
                )
    
    @property
    def database_url_async(self) -> str:
        """
        Get async database URL (for SQLAlchemy 2.0+ async support).
        
        Converts postgresql:// to postgresql+asyncpg:// for async operations.
        """
        if self.DB_URL:
            # Replace sync driver with async driver
            return self.DB_URL.replace("postgresql://", "postgresql+asyncpg://")
        
        # Build async URL from components
        password = self.DB_PASSWORD or ""
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{password}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings with secrets loaded
    """
    return Settings()


# Create global settings instance
settings = get_settings()