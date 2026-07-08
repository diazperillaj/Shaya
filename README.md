# Shaya

Sistema de gestión para una empresa cafetera: cubre el ciclo completo desde la
compra de café pergamino a caficultores, el proceso de maquila/tostado, el
control de inventario, hasta la venta (directa y en ferias).

## Stack

- **Backend:** FastAPI + SQLAlchemy + PostgreSQL (Alembic para migraciones)
- **Chatbot (microservicio):** FastAPI + Pandas + Redis + LLM vía API
  OpenAI-compatible (Groq en desarrollo) — puerto 8005. Arquitectura en
  [`docs/chat_bot.md`](docs/chat_bot.md)
- **Frontend:** React + Vite + TypeScript + Tailwind CSS
- **Despliegue:** Docker Compose (Postgres + backend + chatbot + Redis + Nginx)

## Módulos

Caficultores · Clientes · Productos · Inventario de pergamino · Procesos de
maquila · Costos de producción · Inventario de café tostado · Movimientos
(con reempaque) · Ventas · Ferias · Dashboard · Asistente analítico (chatbot).

## Servicios

| Servicio | Rol | Datos |
|---|---|---|
| `backend` (:8000) | API del negocio (escritura y lectura) | Postgres schema `public` (RW) |
| `chatbot` (:8005) | Asistente analítico: LLM + análisis con Pandas | Postgres `public` (solo lectura), schema `chat` (RW), Redis (memoria) |
| `web` | Nginx: estáticos + proxy `/api/` → backend y `/chat/` → chatbot | — |
| `db` / `redis` | PostgreSQL 16 / Redis 7 (cache reconstruible) | volumen `pgdata` |

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

**Chatbot**
```bash
docker compose up -d redis        # memoria caliente
cd chatbot
python -m venv env && env\Scripts\activate
pip install -r requirements.txt
# Crear chatbot/.env (ver chatbot/.env.example) — incluye la API key de Groq
alembic upgrade head              # crea el schema chat
uvicorn app.main:app --reload --port 8005
```

**Frontend**
```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxy /api -> :8000, /chat -> :8005)
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
