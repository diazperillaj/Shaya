from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# 1️⃣ URL de conexión
DATABASE_URL = "postgresql+psycopg2://postgres:root@localhost:5432/shayatestdb"

# 2️⃣ Engine (puente entre Python y PostgreSQL)
engine = create_engine(DATABASE_URL, echo=True)


Base = declarative_base()

class TestTable(Base):
    __tablename__ = 'test_table'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=True)
    obs = Column(Text, nullable=True)

sessionLocal = sessionmaker(bind=engine)

if __name__ == "__main__":
    # Crear las tablas en la base de datos
    Base.metadata.create_all(engine)


    db = sessionLocal()

    testRows = TestTable(
        id=1,
        name='Prueba',
        obs='esto es una prueba'
    )

    row = db.query(TestTable).filter(TestTable.id == 1).first()

    db.delete(row)
    db.commit()


