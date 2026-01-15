from sqlalchemy import create_engine

DATABASE_URL = "postgresql+psycopg2://postgres:root@localhost:5432/shayatestdb"

engine = create_engine(DATABASE_URL)
