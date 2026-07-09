from fastapi import APIRouter

from app.api.v1.chat.router import router as chat_router

api_router = APIRouter()
api_router.include_router(chat_router)
