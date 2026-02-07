# app/routes/tracking.py
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID
from app import db, models, schemas

router = APIRouter()

def serialize_event(ev: models.Event) -> Dict[str, Any]:
    return {
        "id": str(ev.id),
        "entity_id": str(ev.entity_id),
        "status": ev.event_type,
        "timestamp": ev.timestamp.isoformat() if getattr(ev, "timestamp", None) else None,
        "location": ev.location,
        "actor": ev.actor,
        "details": ev.payload or None,
    }

@router.post("/package", status_code=201)
def create_package(payload: dict, db: Session = Depends(db.get_db)):
    """
    Create a package entity (type=package) and an initial 'created' event.
    Expects payload containing at least:
      - tracking_number (external id)
      - sender, recipient, destination (optional fields)
      - weight_kg (optional)
    """
    tracking_number = payload.get("tracking_number") or payload.get("trackingNumber") or payload.get("external_id")
    if not tracking_number:
        raise HTTPException(status_code=400, detail="tracking_number is required")

    # check existing
    existing = db.query(models.Entity).filter(models.Entity.external_id == tracking_number).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Entity with tracking_number '{tracking_number}' already exists")

    # create entity
    db_entity = models.Entity(
        type="package",
        external_id=tracking_number,
        extra_data={
            "sender": payload.get("sender"),
            "recipient": payload.get("recipient"),
            "destination": payload.get("destination"),
            "weight_kg": payload.get("weight_kg"),
        },
    )
    db.add(db_entity)
    try:
        db.commit()
        db.refresh(db_entity)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create entity: {str(e)}")

    # create an initial event
    try:
        db_event = models.Event(
            entity_id=db_entity.id,
            event_type="created",
            location=None,
            actor=payload.get("creator") or "system",
            payload={"note": "Package created", "meta": payload}
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
    except Exception as e:
        db.rollback()
        # if event creation failed, we may still return created entity, but inform client
        raise HTTPException(status_code=500, detail=f"Entity created but failed to create initial event: {str(e)}")

    # Build return structure similar to what the web UI expects
    package = {
        "tracking_number": tracking_number,
        "status": "created",
        "current_location": None,
        "package": {
            "details": {
                "sender": db_entity.extra_data.get("sender"),
                "recipient": db_entity.extra_data.get("recipient"),
                "destination": db_entity.extra_data.get("destination"),
                "weight_kg": db_entity.extra_data.get("weight_kg"),
            },
            "created_at": getattr(db_entity, "created_at", None).isoformat() if getattr(db_entity, "created_at", None) else None
        },
        "timeline": [serialize_event(db_event)]
    }
    return package

@router.get("/track/{tracking_number}")
def track_package(tracking_number: str, db: Session = Depends(db.get_db)):
    """
    Return package details + timeline for a given tracking_number (external_id).
    """
    entity = db.query(models.Entity).filter_by(external_id=tracking_number).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Package not found")

    events = (
        db.query(models.Event)
        .filter(models.Event.entity_id == entity.id)
        .order_by(models.Event.timestamp)
        .all()
    )

    timeline = [serialize_event(e) for e in events]
    latest = timeline[-1] if timeline else None
    package = {
        "tracking_number": tracking_number,
        "status": latest["status"] if latest else "created",
        "current_location": latest["location"] if latest else None,
        "package": {
            "details": {
                "sender": entity.extra_data.get("sender") if entity.extra_data else None,
                "recipient": entity.extra_data.get("recipient") if entity.extra_data else None,
                "destination": entity.extra_data.get("destination") if entity.extra_data else None,
                "weight_kg": entity.extra_data.get("weight_kg") if entity.extra_data else None,
            },
            "created_at": getattr(entity, "created_at", None).isoformat() if getattr(entity, "created_at", None) else None
        },
        "timeline": timeline
    }
    return package

@router.get("/packages")
def list_packages(status: Optional[str] = None, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(db.get_db)):
    """
    Basic packages listing. If `status` provided, filter by the latest event.status for each package.
    Note: this is a simple implementation; for large datasets you should move to optimized queries.
    """
    q = db.query(models.Entity).filter(models.Entity.type == "package").order_by(models.Entity.created_at.desc()).offset(skip).limit(limit)
    entities = q.all()

    out = []
    for e in entities:
        events = (
            db.query(models.Event)
            .filter(models.Event.entity_id == e.id)
            .order_by(models.Event.timestamp)
            .all()
        )
        latest = events[-1] if events else None
        current_status = latest.event_type if latest else "created"
        if status and status != current_status:
            continue
        out.append({
            "tracking_number": e.external_id,
            "details": {
                "recipient": e.extra_data.get("recipient") if e.extra_data else None,
                "sender": e.extra_data.get("sender") if e.extra_data else None,
            },
            "current_status": current_status,
            "current_location": latest.location if latest else None,
            "last_updated": getattr(latest, "timestamp", None).isoformat() if latest and getattr(latest, "timestamp", None) else None
        })
    return out

@router.get("/stats")
def tracking_stats(db: Session = Depends(db.get_db)):
    """
    Simple stats for dashboard: total_packages and distribution by latest status.
    """
    total = db.query(models.Entity).filter(models.Entity.type == "package").count()
    # naive aggregation: fetch packages and compute status distribution
    entities = db.query(models.Entity).filter(models.Entity.type == "package").all()
    dist = {}
    for e in entities:
        latest_ev = db.query(models.Event).filter(models.Event.entity_id == e.id).order_by(models.Event.timestamp.desc()).first()
        status = latest_ev.event_type if latest_ev else "created"
        dist[status] = dist.get(status, 0) + 1

    return {"total_packages": total, "status_distribution": dist}
