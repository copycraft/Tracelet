# app/routes/entities.py

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from typing import List, Optional
from app import models, schemas, db

# ---------------------------
# Setup proper logger
# ---------------------------
logger = logging.getLogger("tracelet")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

router = APIRouter(tags=["Entities"])


@router.post("/", response_model=schemas.EntityRead, status_code=201)
def create_entity(
    entity: schemas.EntityCreate,
    db: Session = Depends(db.get_db)
):
    """
    Create a new entity (package, shipment, item, or container).
    Defensive and verbose error logging to make debugging easier.
    """
    try:
        # Normalize/validate type into a plain string to store in DB
        if isinstance(entity.type, str):
            type_value = entity.type.lower()
            try:
                type_value = schemas.EntityType(type_value).value
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid entity type '{entity.type}'")
        else:
            # Pydantic likely already converted to Enum
            try:
                type_value = entity.type.value
            except Exception:
                type_value = str(entity.type)

        # Normalize external_id
        external_id = (entity.external_id or str(entity.id) or "").strip()
        if not external_id:
            raise HTTPException(status_code=400, detail="external_id (or id) is required")

        # Ensure no existing entity with same external_id
        existing = db.query(models.Entity).filter(models.Entity.external_id == external_id).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Entity with external_id '{external_id}' already exists"
            )

        # Create DB entity
        db_entity = models.Entity(
            type=type_value,
            external_id=external_id,
            extra_data=entity.extra_data or {},
        )

        db.add(db_entity)
        db.commit()
        db.refresh(db_entity)

        logger.info(f"Created entity {db_entity.id} ({external_id}) of type '{type_value}'")
        return db_entity

    except IntegrityError:
        db.rollback()
        logger.exception("IntegrityError creating entity")
        raise HTTPException(
            status_code=400,
            detail="Database integrity error when creating entity"
        )
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Unhandled exception creating entity")
        raise HTTPException(
            status_code=500,
            detail="Internal server error creating entity"
        )


@router.get("/", response_model=List[schemas.EntityRead])
def list_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: Optional[str] = None,
    type: Optional[str] = None,  # Accept string from query
    db: Session = Depends(db.get_db)
):
    qset = db.query(models.Entity)

    # Filter by type if provided
    if type:
        try:
            type_enum = schemas.EntityType(type.lower())
            qset = qset.filter(models.Entity.type == type_enum.value)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid entity type '{type}'")

    # Search filter
    if q:
        qset = qset.filter(
            (models.Entity.external_id.ilike(f"%{q}%")) |
            (models.Entity.type.ilike(f"%{q}%"))
        )

    return qset.order_by(models.Entity.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{entity_id}", response_model=schemas.EntityRead)
def get_entity(
    entity_id: UUID,
    db: Session = Depends(db.get_db)
):
    entity = db.query(models.Entity).filter_by(id=entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.get("/external/{external_id}", response_model=schemas.EntityRead)
def get_entity_by_external_id(
    external_id: str,
    db: Session = Depends(db.get_db)
):
    entity = db.query(models.Entity).filter_by(external_id=external_id).first()
    if not entity:
        raise HTTPException(
            status_code=404,
            detail=f"Entity with external_id '{external_id}' not found"
        )
    return entity
