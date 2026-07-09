from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "development"
    SERVICE_NAME: str = "shaya-chatbot"

    # ── Base de datos compartida con el backend ──────────────────────
    BUSINESS_DB_HOST: str
    BUSINESS_DB_PORT: int = 5432
    BUSINESS_DB_NAME: str

    # Usuario de solo lectura sobre schema public (negocio)
    BUSINESS_DB_USER: str
    BUSINESS_DB_PASSWORD: str

    # Usuario RW sobre schema chat (historial)
    CHAT_DB_USER: str
    CHAT_DB_PASSWORD: str

    # ── Redis (memoria conversacional caliente) ──────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── Autenticación (mismo SECRET_KEY del backend) ─────────────────
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    FRONTEND_URL: str

    # ── LLM (API OpenAI-compatible) ──────────────────────────────────
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_API_KEY: str
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_MODEL_LIGHT: str = "llama-3.1-8b-instant"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 700

    # ── Barandillas del agente ───────────────────────────────────────
    CHAT_MAX_ITERATIONS: int = 7
    CHAT_HISTORY_WINDOW: int = 30       # mensajes enviados al LLM (cola FIFO)
    CHAT_TOOL_TIMEOUT_S: int = 15
    CHAT_TURN_TIMEOUT_S: int = 90
    CHAT_RATE_LIMIT_PER_MIN: int = 20
    CHAT_MAX_ROWS_PER_TOOL: int = 50
    CHAT_MEMORY_TTL_S: int = 7 * 24 * 3600

    TIMEZONE: str = "America/Bogota"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def business_db_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.BUSINESS_DB_USER}:{self.BUSINESS_DB_PASSWORD}"
            f"@{self.BUSINESS_DB_HOST}:{self.BUSINESS_DB_PORT}/{self.BUSINESS_DB_NAME}"
        )

    @property
    def chat_db_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.CHAT_DB_USER}:{self.CHAT_DB_PASSWORD}"
            f"@{self.BUSINESS_DB_HOST}:{self.BUSINESS_DB_PORT}/{self.BUSINESS_DB_NAME}"
        )


settings = Settings()
