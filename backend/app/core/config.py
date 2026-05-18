from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Unilex AI"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # OpenAI
    OPENAI_API_KEY: str
    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # CORS — production'da sadece frontend origin'i ekle
    ALLOWED_ORIGINS: list[str] = ["*"]

    # Scheduler — periyodik crawl aralığı (saat)
    CRAWL_INTERVAL_HOURS: int = 24

    class Config:
        env_file = ".env"


settings = Settings()
