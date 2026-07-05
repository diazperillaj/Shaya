from fastapi import APIRouter
from app.api.api_v1.users import router as users_router
from app.api.api_v1.auth import router as auth_router
from app.api.api_v1.farmers import router as farmers_router
from app.api.api_v1.customers import router as customers_router
from app.api.api_v1.inventory import router as inventory_router
from app.api.api_v1.products import router as product_router
from app.api.api_v1.processes import router as process_router
from app.api.api_v1.roasted_coffee import router as maquilado_router
from app.api.api_v1.sales import router as sales_router
from app.api.api_v1.dashboard import router as dashboard_router
from app.api.api_v1.fairs import router as fairs_router
from app.api.api_v1.roasted_movements import router as roasted_movements_router
from app.api.api_v1.process_expenses import router as process_expenses_router
from app.api.api_v1.product_expenses import router as product_expenses_router
from app.api.api_v1.general_expenses import router as general_expenses_router
from app.api.api_v1.expense_categories import router as expense_categories_router
from app.api.api_v1.payment_methods import router as payment_methods_router

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
api_router.include_router(process_router.router, prefix="/process", tags=["process"])
api_router.include_router(maquilado_router.router, prefix="/maquilado", tags=["maquilado"])
api_router.include_router(sales_router.router, prefix="/sales", tags=["sales"])
api_router.include_router(dashboard_router.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(fairs_router.router, prefix="/fairs", tags=["fairs"])
api_router.include_router(roasted_movements_router.router, prefix="/roasted-movements", tags=["roasted-movements"])
api_router.include_router(process_expenses_router.router, prefix="/process-expenses", tags=["process-expenses"])
api_router.include_router(product_expenses_router.router, prefix="/product-expenses", tags=["product-expenses"])
api_router.include_router(general_expenses_router.router, prefix="/general-expenses", tags=["general-expenses"])
api_router.include_router(expense_categories_router.router, prefix="/expense-categories", tags=["expense-categories"])
api_router.include_router(payment_methods_router.router, prefix="/payment-methods", tags=["payment-methods"])