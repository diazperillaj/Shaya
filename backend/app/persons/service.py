from sqlalchemy import text
from app.core.database import engine

def create_person(data: dict):
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO persons 
                (full_name, document, phone, email, observation)
                VALUES (:full_name, :document, :phone, :email, :observation)
            """),
            data
        )
        conn.commit()
