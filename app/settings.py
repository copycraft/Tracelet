# app/settings.py
import logging
from pydantic_settings import BaseSettings
import os

logger = logging.getLogger("tracelet.settings")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class Settings(BaseSettings):
    POSTGRES_USER: str = "tracelet_user"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "tracelet_db"
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT: int = 5432
    SQL_ECHO: bool = False

    class Config:
        env_file = ".env"


settings = Settings()

logger.info(
    f"Settings loaded: DB={settings.POSTGRES_DB} "
    f"HOST={settings.POSTGRES_HOST} PORT={settings.POSTGRES_PORT}"
)


def get_database_url() -> str:
    return (
        f"postgresql+psycopg2://{settings.POSTGRES_USER}:"
        f"{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:"
        f"{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )