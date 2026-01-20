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
        "http://localhost:5173",  # Vite
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

#Ruta inicial de los endpoints
app.include_router(api_router, prefix="/api/v1")

