from fastapi import FastAPI
from app.api.endpoints import router

app = FastAPI(
    title="Medical Entity Recognition API",
    description="API for recognizing and coding medical entities using LLM-based analysis",
    version="1.0.0"
)

app.include_router(router) 