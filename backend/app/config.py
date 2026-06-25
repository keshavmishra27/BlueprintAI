import os
from functools import lru_cache
from dotenv import load_dotenv
load_dotenv(override=True)
@lru_cache
def get_settings():
    return Settings()
class Settings:
    def __init__(self):
        self.api_key: str | None = os.getenv("API_KEY") or None
        self.cors_origins: list[str] = [
            o.strip()
            for o in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:8765,http://127.0.0.1:8765,http://localhost:5173,http://127.0.0.1:5173",
            ).split(",")
            if o.strip()
        ]
        self.rate_limit_default: str = os.getenv("RATE_LIMIT_DEFAULT", "30/minute")
        self.rate_limit_expensive: str = os.getenv("RATE_LIMIT_EXPENSIVE", "5/minute")
        self.github_token: str | None = os.getenv("GITHUB_TOKEN") or None
        self.search_enabled: bool = os.getenv("SEARCH_ENABLED", "true").lower() == "true"
