# app/routes/events.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from typing import List, Optional
from app import models, schemas, db

router = APIRouter(tags=["Events"])


@router.post("/", response_model=schemas.EventRead, status_code=201)
def create_event(event: schemas.EventCreate, db: Session = Depends(db.get_db)):
    # ensure the referenced entity exists
    entity = db.query(models.Entity).filter(models.Entity.id == event.entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # normalize event_type whether it's an Enum or a string
    event_type_value = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)

    db_event = models.Event(
        entity_id=event.entity_id,
        event_type=event_type_value,
        location=event.location,
        actor=event.actor,
        payload=event.payload
    )

    # Use explicit commit/rollback instead of nested transactions
    db.add(db_event)
    try:
        db.commit()
        db.refresh(db_event)
    except IntegrityError:
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=400, detail="Database integrity error when creating event")
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")

    return db_event


@router.get("/entity/{entity_id}", response_model=List[schemas.EventRead])
def get_entity_events(entity_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(db.get_db)):
    entity = db.query(models.Entity).filter(models.Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    events = db.query(models.Event).filter(models.Event.entity_id == entity_id) \
        .order_by(models.Event.timestamp) \
        .offset(skip).limit(limit).all()
    return events


@router.get("/{event_id}", response_model=schemas.EventRead)
def get_event(event_id: UUID, db: Session = Depends(db.get_db)):
    event = db.query(models.Event).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get("/", response_model=List[schemas.EventRead])
def list_events(skip: int = 0, limit: int = 100,
                event_type: Optional[schemas.PackageStatus] = None,
                location: Optional[str] = None,
                db: Session = Depends(db.get_db)):
    qset = db.query(models.Event)
    if event_type:
        qset = qset.filter(models.Event.event_type == event_type.value)
    if location:
        qset = qset.filter(models.Event.location.ilike(f"%{location}%"))
    return qset.order_by(models.Event.timestamp.desc()).offset(skip).limit(limit).all()


@router.delete("/{event_id}")
def delete_event(event_id: UUID, db: Session = Depends(db.get_db)):
    event = db.query(models.Event).filter_by(id=event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    try:
        db.delete(event)
        db.commit()
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to delete event: {str(e)}")
    return {"status": "deleted", "event_id": str(event_id)}
