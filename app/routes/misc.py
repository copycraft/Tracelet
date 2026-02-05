from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.db import engine
from app.utils import get_api_version

router = APIRouter()


@router.get("/health", summary="Check API and DB health")
async def health_check():
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_status = "ok"
    except Exception:
        db_status = "unreachable"

    return JSONResponse({"api": "ok", "database": db_status})


@router.get("/version", summary="Get API version")
async def version():
    """
    Returns the current API version from pyproject.toml.
    """
    return {"version": get_api_version()}
