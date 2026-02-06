# app/routes/entities.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app import models, schemas, db

router = APIRouter(tags=["Entities"])

# Create
@router.post("/", response_model=schemas.EntityRead)
def create_entity(entity: schemas.EntityCreate, db: Session = Depends(db.get_db)):
    # make sure external_id is present and unique if you require it
    db_entity = models.Entity(
        type=entity.type,
        external_id=entity.external_id or "",
        extra_data=entity.extra_data,
    )
    db.add(db_entity)
    try:
        db.commit()
        db.refresh(db_entity)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating entity: {str(e)}")
    return db_entity


# List with pagination
@router.get("/", response_model=List[schemas.EntityRead])
def list_entities(skip: int = 0, limit: int = 100, q: str | None = None, db: Session = Depends(db.get_db)):
    qset = db.query(models.Entity)
    if q:
        # basic filter on external_id or type
        qset = qset.filter(
            (models.Entity.external_id.ilike(f"%{q}%")) |
            (models.Entity.type.ilike(f"%{q}%"))
        )
    entities = qset.offset(skip).limit(limit).all()
    return entities


# Read
@router.get("/{entity_id}", response_model=schemas.EntityRead)
def get_entity(entity_id: UUID, db: Session = Depends(db.get_db)):
    entity = db.query(models.Entity).filter_by(id=entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


# Update (PATCH)
@router.patch("/{entity_id}", response_model=schemas.EntityRead)
def update_entity(entity_id: UUID, update: schemas.EntityUpdate, db: Session = Depends(db.get_db)):
    entity = db.query(models.Entity).filter_by(id=entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    if update.type is not None:
        entity.type = update.type
    if update.external_id is not None:
        entity.external_id = update.external_id
    if update.extra_data is not None:
        entity.extra_data = update.extra_data

    try:
        db.commit()
        db.refresh(entity)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating entity: {str(e)}")
    return entity


# Delete
@router.delete("/{entity_id}")
def delete_entity(entity_id: UUID, force: bool = Query(False), db: Session = Depends(db.get_db)):
    entity = db.query(models.Entity).filter_by(id=entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # If not forced, prevent deleting when links exist
    if not force:
        has_links = db.query(models.EntityLink).filter(
            (models.EntityLink.parent_id == entity_id) | (models.EntityLink.child_id == entity_id)
        ).first()
        if has_links:
            raise HTTPException(status_code=400, detail="Entity has links. Use ?force=true to delete.")

    try:
        db.delete(entity)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete entity: {str(e)}")

    return {"status": "deleted", "entity_id": str(entity_id)}
