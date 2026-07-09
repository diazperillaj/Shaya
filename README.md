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

**Chatbot** (siempre sobre Docker — sin modo local)
```bash
# 1) Una sola vez por entorno: roles de DB (solo-lectura + schema chat)
docker compose exec -T db psql -U <DB_USER> -d <DB_NAME> \
  -v ro_pass='<CHATBOT_RO_PASSWORD>' -v app_pass='<CHATBOT_APP_PASSWORD>' \
  -f - < chatbot/scripts/init_db_roles.sql

# 2) Variables nuevas en el .env raíz: CHATBOT_RO_PASSWORD, CHATBOT_APP_PASSWORD,
#    LLM_API_KEY (Groq). Luego:
docker compose up -d --build chatbot redis

# Verificar: http://localhost:8005/health  (o /chat/health vía nginx)
# Cada cambio en chatbot/ se prueba reconstruyendo: docker compose up -d --build chatbot
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
