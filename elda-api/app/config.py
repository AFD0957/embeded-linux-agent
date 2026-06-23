"""Application settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ELDA_", env_file=".env", extra="ignore")

    database_url: str = ""
    redis_url: str = "redis://127.0.0.1:6379/0"
    milvus_host: str = "127.0.0.1"
    milvus_port: int = 19530
    minio_endpoint: str = "127.0.0.1:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket: str = "elda-artifacts"
    minio_secure: bool = False
    executor_poll_timeout: int = 25
    build_max_fix_rounds: int = 10
    app_version: str = "0.3.0"


settings = Settings()
