# app/routes/__init__.py

from fastapi import APIRouter

from . import entities, events, links, trace, misc, tracking, tracking_pdf  # <-- added tracking_pdf

router = APIRouter()

router.include_router(entities.router, prefix="/entities", tags=["Entities"])
router.include_router(events.router, prefix="/events", tags=["Events"])
router.include_router(links.router, prefix="/links", tags=["Links"])
router.include_router(trace.router, prefix="/trace", tags=["Trace"])
router.include_router(tracking.router, prefix="/tracking", tags=["Tracking"])
router.include_router(tracking_pdf.router, prefix="/tracking_pdf", tags=["Tracking PDF"])
router.include_router(misc.router, prefix="", tags=["Misc"])
