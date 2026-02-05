# app/routes/__init__.py
from fastapi import APIRouter

from . import entities, events, links, trace

router = APIRouter()

router.include_router(entities.router, prefix="/entities", tags=["Entities"])
router.include_router(events.router, prefix="/events", tags=["Events"])
router.include_router(links.router, prefix="/links", tags=["Links"])
router.include_router(trace.router, prefix="/trace", tags=["Trace"])
