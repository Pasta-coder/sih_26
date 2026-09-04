from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 480

    # Database
    database_url: str = "sqlite:///./compliance.db"

    # Tier 1 API keys
    gst_api_key: str = ""
    gst_api_base_url: str = "https://api.sandbox.co.in/gst"
    pan_api_key: str = ""
    pan_api_base_url: str = "https://api.sandbox.co.in/kyc/pan"
    epfo_api_key: str = ""
    epfo_api_base_url: str = "https://api.deepvue.tech/v1"
    mca_api_key: str = ""
    mca_api_base_url: str = "https://api.authbridge.com/mca"

    # File uploads
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 20

    # CORS
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    # Feature flags
    use_real_tier1_apis: bool = False

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
