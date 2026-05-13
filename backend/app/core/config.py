from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ruta al .env en la raíz del proyecto
ENV_FILE_PATH = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str = "SPHERE Backend Orchestrator"
    API_V1_STR: str = "/api/v1"

    # Entorno: "production" (default, estricto) | "development" (laxo, dev-only)
    ENVIRONMENT: str = "production"

    # Variable obligatoria
    MONGODB_URL: str
    DB_NAME: str = "sphere_db"

    # CORS — en producción, set to comma-separated list of frontend URLs
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # n8n - Workflow Automation
    N8N_BASE_URL: str = "http://n8n:5678"
    N8N_WEBHOOK_SECRET: str = ""
    N8N_API_KEY: str = ""  # API key para gestionar workflows (X-N8N-API-KEY)

    # Firebase Auth
    FIREBASE_CREDENTIALS_PATH: str = ""

    # Cifrado de tokens OAuth en reposo
    FERNET_KEY: str = ""

    # OAuth Providers
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    NOTION_CLIENT_ID: str = ""
    NOTION_CLIENT_SECRET: str = ""
    SLACK_CLIENT_ID: str = ""
    SLACK_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_BASE_URL: str = "http://localhost:8000/api/v1/integrations"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 30
    TOKEN_BUDGET_DAILY_DEFAULT: int = 100_000
    TOKEN_BUDGET_RESET_HOUR_UTC: int = 0

    # GridFS Quota
    GRIDFS_QUOTA_MB_PER_USER: int = 500

    # Timeouts
    OPENAI_TIMEOUT: float = 15.0
    DEEPSEEK_TIMEOUT: float = 60.0
    EXTERNAL_API_TIMEOUT: float = 30.0

    # DeepSeek
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # OpenAI
    OPENAI_API_KEY: str = ""

    # Stripe (pagos)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_STARTER: str = ""
    STRIPE_PRICE_PREMIUM: str = ""
    STRIPE_PRICE_TOPUP_FREE: str = ""
    STRIPE_PRICE_TOPUP_STARTER: str = ""
    STRIPE_PRICE_TOPUP_PREMIUM_1K: str = ""
    STRIPE_PRICE_TOPUP_PREMIUM_2K: str = ""
    STRIPE_PRICE_TOPUP_PREMIUM_10K: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    @property
    def topup_messages_map(self) -> dict[str, int]:
        """Mapeo plan_id -> mensajes que otorga ese top-up."""
        return {
            "topup_free": 100,
            "topup_starter": 700,
            "topup_premium_1k": 1000,
            "topup_premium_2k": 2000,
            "topup_premium_10k": 10000,
        }

    @property
    def plan_messages_map(self) -> dict[str, int]:
        """Mapeo plan_id -> mensajes mensuales que otorga el plan."""
        return {
            "free": 5,
            "starter": 1000,
            "premium": 2000,
        }

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() in ("development", "dev", "local")

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=str(ENV_FILE_PATH),
        extra="ignore",  # Ignorar variables extra del .env
    )


settings = Settings()
