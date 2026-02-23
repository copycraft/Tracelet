# app/main.py
import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("tracelet")

app = FastAPI(
    title="Tracelet API",
    description="Universal parcel tracking system for entities, events, and relationships",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

logger.info("Initializing Tracelet API...")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # internal usage
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    process_time = round((time.time() - start_time) * 1000, 2)

    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} "
        f"time={process_time}ms "
        f"client={request.client.host}"
    )

    return response

app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Root"])
def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Tracelet API is running",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

@app.on_event("startup")
async def startup_event():
    logger.info("Tracelet API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Tracelet API shutting down")