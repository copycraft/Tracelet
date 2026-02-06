# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router as api_router

app = FastAPI(
    title="Tracelet API",
    description="Universal parcel tracking system for entities, events, and relationships",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - configure as needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["Root"])
def root():
    """
    Root endpoint - confirms API is running.
    """
    return {
        "message": "Tracelet API is running",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }