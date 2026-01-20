from sqlalchemy.orm import sessionmaker
from app.core.db.base import engine

# SessionLocal será nuestra "fábrica" de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
