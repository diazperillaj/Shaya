from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# ── Engine del NEGOCIO: usuario chatbot_ro, solo lectura ─────────────
# Doble cinturón: además de que el rol solo tiene SELECT, la sesión se
# abre como read-only y con timeout de sentencia (consultas colgadas
# no bloquean el servicio).
business_engine = create_engine(
    settings.business_db_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    connect_args={
        "options": "-c default_transaction_read_only=on -c statement_timeout=10000"
    },
)

# ── Engine del CHAT: usuario chatbot_app, schema chat ────────────────
chat_engine = create_engine(
    settings.chat_db_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    connect_args={"options": "-c search_path=chat,public"},
)

SessionLocal = sessionmaker(bind=chat_engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Base de los modelos propios del chatbot (viven en el schema chat)."""


def get_db():
    """Dependencia FastAPI: sesión sobre el schema chat."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
