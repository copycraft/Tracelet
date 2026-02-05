# app/main.py
from fastapi import FastAPI
from app.routes import router as api_router  # combined router

app = FastAPI(
    title="Tracelet API",
    description="Universal tracking system for entities and events",
    version="0.1.0"
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Tracelet API is running"}
