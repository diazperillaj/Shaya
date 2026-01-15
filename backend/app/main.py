from fastapi import FastAPI
from app.persons.routes import router as persons_router

app = FastAPI()

app.include_router(persons_router)
