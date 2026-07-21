from fastapi import FastAPI
from app.api.api_v1.api_v1 import api_router

#Seguridad CORS
from fastapi.middleware.cors import CORSMiddleware

from app.core.exceptions.handlers import register_exception_handlers

app = FastAPI(title="Shaya Project")

#Seguridad CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    # Permite acceder desde otros dispositivos de la red local (ej. celular)
    allow_origin_regex=r"http://(192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}):5173",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


register_exception_handlers(app)


@app.get("/")
def root():
    return {"message": "Shaya API running"}

@app.get("/api/v1")
def api_root():
    return {"message": "API v1 working"}

#Ruta inicial de los endpoints
app.include_router(api_router, prefix="/api/v1")
