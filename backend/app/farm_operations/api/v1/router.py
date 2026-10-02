from fastapi import APIRouter

"""
Router principal del módulo de cultivo.

Compone los routers de cada recurso del módulo (fincas, lotes, ciclos…).
Se monta en `api_v1.py` bajo el prefijo `/farm`; cada sub-router define su
propio prefijo y su etiqueta para Swagger (`farm-plots`, `farm-harvests`…).
"""

farm_router = APIRouter()
