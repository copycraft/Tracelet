# app / routes / misc

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.db import engine
from app.utils import get_api_version

router = APIRouter()


@router.get("/health", summary="Check API and DB health")
async def health_check():
    """
    Health check endpoint to verify API and database connectivity.

    Returns:
    - api: Always "ok" if the API is responding
    - database: "ok" if database is reachable, "unreachable" otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = "unreachable"
        return JSONResponse(
            status_code=503,
            content={
                "api": "ok",
                "database": db_status,
                "error": str(e)
            }
        )

    return JSONResponse({
        "api": "ok",
        "database": db_status
    })


@router.get("/version", summary="Get API version")
async def version():
    """
    Returns the current API version from pyproject.toml.
    """
    return {"version": get_api_version()}