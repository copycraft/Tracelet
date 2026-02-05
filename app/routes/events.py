from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app import models, schemas, db

router = APIRouter(tags=["Events"])

@router.post("/", response_model=schemas.EventRead)
def create_event(event: schemas.EventCreate, db: Session = Depends(db.get_db)):
    # Check entity exists
    entity = db.query(models.Entity).filter(models.Entity.id == event.entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    db_event = models.Event(
        entity_id=event.entity_id,
        event_type=event.event_type,
        location=event.location,
        actor=event.actor,
        payload=event.payload
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.get("/entity/{entity_id}", response_model=list[schemas.EventRead])
def get_entity_events(entity_id: UUID, db: Session = Depends(db.get_db)):
    events = db.query(models.Event).filter(models.Event.entity_id == entity_id).order_by(models.Event.timestamp).all()
    return events
