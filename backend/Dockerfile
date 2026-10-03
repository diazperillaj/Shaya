FROM python:3.13-slim AS base

WORKDIR /app

# Dependencias primero para aprovechar la caché de capas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Desarrollo: pruebas y herramientas (generador de datos sintéticos) ──
FROM base AS dev

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

# ── Producción: la última etapa es la que se construye por defecto ──────
FROM base AS production

COPY . .

EXPOSE 8000

# El comando real (migraciones + uvicorn) lo define docker-compose
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
