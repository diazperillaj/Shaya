FROM python:3.13-slim

WORKDIR /app

# Dependencias primero para aprovechar la caché de capas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# El comando real (migraciones + uvicorn) lo define docker-compose
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
