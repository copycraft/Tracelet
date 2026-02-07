# app / routes / events

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from app import models, schemas, db

router = APIRouter(tags=["Events"])


@router.post("/", response_model=schemas.EventRead, status_code=201)
def create_event(
        event: schemas.EventCreate,
        db: Session = Depends(db.get_db)
):
    """
    Create a new event for an entity.

    Events represent status changes, movements, or actions taken on an entity.
    """
    # Check entity exists
    entity = db.query(models.Entity).filter(models.Entity.id == event.entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    db_event = models.Event(
        entity_id=event.entity_id,
        event_type=event.event_type.value,
        location=event.location,
        actor=event.actor,
        payload=event.payload
    )

    db.add(db_event)

    try:
        db.commit()
        db.refresh(db_event)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating event: {str(e)}"
        )

    return db_event


@router.get("/entity/{entity_id}", response_model=List[schemas.EventRead])
def get_entity_events(
        entity_id: UUID,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        db: Session = Depends(db.get_db)
):
    """
    Get all events for a specific entity, ordered by timestamp.
    """
    # Check entity exists
    entity = db.query(models.Entity).filter(models.Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    events = (
        db.query(models.Event)
        .filter(models.Event.entity_id == entity_id)
        .order_by(models.Event.timestamp)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return events


@router.get("/{event_id}", response_model=schemas.EventRead)
def get_event(
        event_id: UUID,
        db: Session = Depends(db.get_db)
):
    """
    Get a specific event by its UUID.
    """
    event = db.query(models.Event).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/", response_model=List[schemas.EventRead])
def list_events(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        event_type: Optional[schemas.PackageStatus] = None,
        location: Optional[str] = None,
        db: Session = Depends(db.get_db)
):
    """
    List all events with optional filtering.

    - **event_type**: Filter by event type (e.g., picked_up, delivered)
    - **location**: Filter by location (partial match)
    """
    qset = db.query(models.Event)

    if event_type:
        qset = qset.filter(models.Event.event_type == event_type.value)

    if location:
        qset = qset.filter(models.Event.location.ilike(f"%{location}%"))

    events = (
        qset
        .order_by(models.Event.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return events


@router.delete("/{event_id}")
def delete_event(
        event_id: UUID,
        db: Session = Depends(db.get_db)
):
    """
    Delete an event.
    """
    event = db.query(models.Event).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    try:
        db.delete(event)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete event: {str(e)}"
        )

    return {
        "status": "deleted",
        "event_id": str(event_id)
    }