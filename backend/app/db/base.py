from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

DATABASE_URL = "postgresql+psycopg2://postgres:root@localhost:5432/shayatestdb"

# Motor de conexión
engine = create_engine(DATABASE_URL, echo=True)

# Base declarativa para los modelos
Base = declarative_base()