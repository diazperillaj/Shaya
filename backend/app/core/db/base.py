from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

#DATABASE_URL = 'postgresql://neondb_owner:npg_MQRZx1TpgqI9@ep-dark-bird-ahzipptl-pooler.c-3.us-east-1.aws.neon.tech/shayadbtest?sslmode=require&channel_binding=require'
DATABASE_URL = 'postgresql://postgres:root@localhost:5432/shayatestdb'
# Motor de conexión
engine = create_engine(DATABASE_URL, echo=True)

# Base declarativa para los modelos
Base = declarative_base()