from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app import models, schemas, db

router = APIRouter()

@router.post("/", response_model=schemas.EntityRead)
def create_entity(entity: schemas.EntityCreate, db: Session = Depends(db.get_db)):
    db_entity = models.Entity(
        type=entity.type,
        external_id=entity.external_id,
        extra_data=entity.extra_data
    )
    db.add(db_entity)
    try:
        db.commit()
        db.refresh(db_entity)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating entity: {str(e)}")
    return db_entity

@router.get("/", response_model=list[schemas.EntityRead])
def list_entities(skip: int = 0, limit: int = 100, db: Session = Depends(db.get_db)):
    entities = db.query(models.Entity).offset(skip).limit(limit).all()
    return entities

@router.get("/{entity_id}", response_model=schemas.EntityRead)
def get_entity(entity_id: UUID, db: Session = Depends(db.get_db)):
    entity = db.query(models.Entity).filter(models.Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity
