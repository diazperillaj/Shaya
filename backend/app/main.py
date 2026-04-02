from fastapi import FastAPI
from app.api.api_v1.api_v1 import api_router

#Seguridad CORS
from fastapi.middleware.cors import CORSMiddleware

from app.models.inventory import Inventory
from app.models.parchment import Parchment
from app.models.processed import Processed
from app.models.product import Product
from app.models.toll_process import TollProcess
from app.models.sale import Sale
from app.models.user import User 
from app.models.sale_detail import SaleDetail




from app.core.exceptions.handlers import register_exception_handlers

app = FastAPI(title="Shaya Project")

#Seguridad CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


register_exception_handlers(app)

#Ruta inicial de los endpoints
app.include_router(api_router, prefix="/api/v1")

