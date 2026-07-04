# Shaya

Sistema de gestión para una empresa cafetera: cubre el ciclo completo desde la
compra de café pergamino a caficultores, el proceso de maquila/tostado, el
control de inventario, hasta la venta (directa y en ferias).

## Stack

- **Backend:** FastAPI + SQLAlchemy + PostgreSQL (Alembic para migraciones)
- **Frontend:** React + Vite + TypeScript + Tailwind CSS
- **Despliegue:** Docker Compose (Postgres + backend + Nginx)

## Módulos

Caficultores · Clientes · Productos · Inventario de pergamino · Procesos de
maquila · Costos de producción · Inventario de café tostado · Movimientos
(con reempaque) · Ventas · Ferias · Dashboard.

## Desarrollo local

**Backend**
```bash
cd backend
python -m venv env && env\Scripts\activate      # Windows
pip install -r requirements.txt
# Crear backend/.env (ver .env.example en la raíz para las variables)
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxy /api -> :8000)
```

## Despliegue con Docker

```bash
cp .env.example .env      # ajustar credenciales y WEB_PORT
docker compose up -d --build
```

La aplicación queda disponible en el puerto definido por `WEB_PORT`.
Restaurar un backup de la base:

```bash
docker compose up -d db
docker compose exec -T db psql -U <DB_USER> -d <DB_NAME> < backup.sql
docker compose up -d
```
