from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

DATABASE_URL = (
    f"postgresql://{settings.DB_USER}:"
    f"{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:"
    f"{settings.DB_PORT}/"
    f"{settings.DB_NAME}"
)

# Motor de conexión
engine = create_engine(DATABASE_URL, echo=True)

# Base declarativa para los modelos
Base = declarative_base()



