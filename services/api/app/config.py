from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://payroll:payroll@localhost:5432/payroll"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "local-development-secret-change-me"
    jwt_expires_minutes: int = 480
    events_queue: str = "payroll:events"
    cors_origins: str = "http://localhost:8080,http://localhost:5173"


settings = Settings()
