from sqlalchemy.orm import sessionmaker
from app.core.db.base import engine

# SessionLocal será nuestra "fábrica" de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependencia que proporciona una sesión activa de base de datos.

    Yields:
        Session: Sesión de SQLAlchemy activa.

    Garantiza:
        El cierre correcto de la sesión al finalizar la petición.
    """
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        print("ERROR en get_db:", e)
        raise
    finally:
        db.close()