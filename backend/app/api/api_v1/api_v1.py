from fastapi import APIRouter
from app.api.api_v1.users import router as users_router
from app.api.api_v1.auth import router as auth_router
from app.api.api_v1.farmers import router as farmers_router
from app.api.api_v1.customers import router as customers_router
from app.api.api_v1.inventory import router as inventory_router
from app.api.api_v1.products import router as product_router
from app.api.api_v1.fast_sale import router as fast_sale_router

"""
Router principal de la API versión 1.

Este archivo centraliza la inclusión de los routers
de los distintos módulos del sistema (usuarios, roles, etc.).

Cada router se incluye con:
- Un prefijo de ruta
- Un conjunto de etiquetas para la documentación Swagger
"""

api_router = APIRouter()

api_router.include_router(users_router.router, prefix="/users", tags=["users"])
api_router.include_router(auth_router.router, prefix="/auth", tags=["auth"])
api_router.include_router(farmers_router.router, prefix="/farmers", tags=["farmers"])
api_router.include_router(customers_router.router, prefix="/customers", tags=["customers"])
api_router.include_router(inventory_router.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(product_router.router, prefix="/products", tags=["product"])
api_router.include_router(fast_sale_router.router, prefix="/fast-sale", tags=["fast-sales"])