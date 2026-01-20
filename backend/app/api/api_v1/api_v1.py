from fastapi import APIRouter
from app.api.api_v1.users import router

"""
Router principal de la API versión 1.

Este archivo centraliza la inclusión de los routers
de los distintos módulos del sistema (usuarios, roles, etc.).

Cada router se incluye con:
- Un prefijo de ruta
- Un conjunto de etiquetas para la documentación Swagger
"""

api_router = APIRouter()
api_router.include_router(router.router, prefix="/users", tags=["users"])
