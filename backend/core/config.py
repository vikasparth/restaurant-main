from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from uuid import UUID
from pathlib import Path


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
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
    github_api_base_url: str = "https://api.github.com"
    github_api_version: str = "2022-11-28"

    # --- Render (MCP log access) ---
    render_api_key: str = ""
    render_service_id: str = ""
    render_owner_id: str = ""
    render_api_base_url: str = "https://api.render.com/v1"

    # --- Production service URL ---
    production_url: str = "https://restaurant-main.onrender.com"

    # --- Provider status pages ---
    resend_status_url: str = "https://resend-status.com/api/v2/status.json"
    twilio_status_url: str = "https://status.twilio.com/api/v2/status.json"

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
