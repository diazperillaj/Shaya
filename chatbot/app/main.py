from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.db import business_engine, chat_engine
from app.core.logging import logger, setup_logging
from app.core.redis import get_redis

setup_logging()

app = FastAPI(
    title="Shaya Chatbot",
    description="Asistente analítico del negocio (microservicio).",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health() -> JSONResponse:
    """Estado del servicio y sus 4 dependencias (§5 del doc maestro)."""
    checks: dict[str, str] = {}

    try:
        with business_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["db_negocio"] = "ok"
    except Exception as exc:  # noqa: BLE001 — el health reporta, no explota
        logger.error("Health db_negocio: %s", exc)
        checks["db_negocio"] = "error"

    try:
        with chat_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["db_chat"] = "ok"
    except Exception as exc:
        logger.error("Health db_chat: %s", exc)
        checks["db_chat"] = "error"

    try:
        await get_redis().ping()
        checks["redis"] = "ok"
    except Exception as exc:
        logger.error("Health redis: %s", exc)
        checks["redis"] = "error"

    checks["llm"] = "ok" if settings.LLM_API_KEY and settings.LLM_MODEL else "sin_configurar"

    healthy = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "ok" if healthy else "degradado",
            "servicio": settings.SERVICE_NAME,
            "entorno": settings.ENV,
            "dependencias": checks,
        },
    )
