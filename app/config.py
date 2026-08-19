from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    SECRET_KEY: str = "CHANGE_ME_TO_A_RANDOM_STRING"
    ADMIN_USER: str = "admin"
    ADMIN_PASS: str = "changeme123"

    DATABASE_URL: str = "sqlite+aiosqlite:///./data/upserarch.db"

    UPLOAD_DIR: str = "/app/uploads"
    DATA_DIR: str = "/app/data"
    MAX_FILE_SIZE: int = 52428800  # 50MB
    ALLOWED_EXTENSIONS: str = "pdf"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()


def ensure_directories():
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
