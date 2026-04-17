from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from uuid import UUID


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Database ---
    database_url: str

    # --- Supabase Auth ---
    supabase_url: str
    supabase_jwt_secret: str

    # --- CORS ---
    allowed_origins: str = "http://localhost:5173"

    # --- App ---
    environment: str = "development"
    location_id: UUID

    # --- Email (Resend) ---
    resend_api_key: str = ""
    resend_from_email: str = "onboarding@resend.dev"
    owner_email: str = ""

    # --- WhatsApp (Twilio) ---
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"
    owner_whatsapp: str = ""

    # --- Internal API security ---
    internal_token: str = ""

    # --- Feature flags ---
    notifications_enabled: bool = True

    # --- Monitoring ---
    monitor_window_hours: int = 6
    monitor_error_rate_threshold: float = 0.05
    monitor_latency_p95_threshold_ms: int = 2000
    monitor_notification_failure_threshold: int = 2

    # --- GitHub (monitoring alerts) ---
    github_token: str = ""
    github_repo: str = ""

    # --- Render (MCP log access) ---
    render_api_key: str = ""
    render_service_id: str = ""
    render_owner_id: str = ""

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]


# Single instance — imported everywhere
settings = Settings()
