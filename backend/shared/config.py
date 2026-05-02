import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    environment: str = Field(default="development", alias="ENVIRONMENT")
    project_id: str = Field(default="devcollab-local", alias="GCP_PROJECT_ID")
    mongodb_uri: str = Field(default="mongodb://localhost:27017/devcollab", alias="MONGODB_URI")
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    pubsub_project: str = Field(default="devcollab-local", alias="PUBSUB_PROJECT")
    gcs_bucket: str = Field(default="devcollab-uploads", alias="GCS_BUCKET")
    firebase_project_id: str = Field(default="devcollab-local", alias="FIREBASE_PROJECT_ID")
    allowed_origins: list[str] = Field(default=["http://localhost:5173"], alias="ALLOWED_ORIGINS")
    secret_manager_enabled: bool = Field(default=False, alias="SECRET_MANAGER_ENABLED")

    model_config = {"env_file": ".env", "case_sensitive": False, "populate_by_name": True}

    @classmethod
    def from_secret_manager(cls) -> "Settings":
        """In production, fetch secrets from GCP Secret Manager."""
        instance = cls()
        if instance.secret_manager_enabled:
            try:
                from google.cloud import secretmanager
                client = secretmanager.SecretManagerServiceClient()
                project = instance.project_id

                def _get_secret(name: str) -> str:
                    path = f"projects/{project}/secrets/{name}/versions/latest"
                    response = client.access_secret_version(request={"name": path})
                    return response.payload.data.decode("utf-8").strip()

                instance.mongodb_uri = _get_secret("devcollab-mongodb-uri")
                instance.redis_host = _get_secret("devcollab-redis-host")
            except Exception as e:
                import logging
                logging.warning(f"Secret Manager fetch failed, using env vars: {e}")
        return instance


@lru_cache()
def get_settings() -> Settings:
    return Settings.from_secret_manager()


settings = get_settings()
