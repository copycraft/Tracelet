# app/routes/entities.py
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from typing import List, Optional
from app import models, schemas, db

logger = logging.getLogger("tracelet.entities")

router = APIRouter(tags=["Entities"])


@router.post("/", response_model=schemas.EntityRead, status_code=201)
def create_entity(entity: schemas.EntityCreate, db: Session = Depends(db.get_db)):
    try:
        # Normalize type to string (handle Enum or plain string)
        type_value = entity.type.value.lower() if hasattr(entity.type, "value") else str(entity.type).lower()

        # Defensive external_id handling: only use id if it's not None
        external_id = (entity.external_id or (str(entity.id) if entity.id is not None else None) or "").strip()
        if not external_id:
            raise HTTPException(status_code=400, detail="external_id (or id) is required")

        existing = db.query(models.Entity).filter(models.Entity.external_id == external_id).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Entity with external_id '{external_id}' already exists")

        db_entity = models.Entity(type=type_value, external_id=external_id, extra_data=entity.extra_data or {})

        # Use explicit commit instead of starting a new transaction with db.begin()
        db.add(db_entity)
        try:
            db.commit()
            db.refresh(db_entity)
        except IntegrityError:
            # rollback and convert to HTTP 400
            try:
                db.rollback()
            except Exception:
                logger.debug("rollback failed or not needed")
            logger.exception("IntegrityError creating entity")
            raise HTTPException(status_code=400, detail="Database integrity error when creating entity")
        except Exception:
            try:
                db.rollback()
            except Exception:
                logger.debug("rollback failed or not needed")
            logger.exception("Unhandled exception creating entity (commit/refresh)")
            raise HTTPException(status_code=500, detail="Internal server error creating entity")

        logger.info(f"Created entity {db_entity.id} ({external_id}) of type '{type_value}'")
        return db_entity

    except HTTPException:
        # propagate expected HTTP errors
        raise
    except Exception:
        # any other unexpected error
        try:
            db.rollback()
        except Exception:
            logger.debug("rollback failed or not needed")
        logger.exception("Unhandled exception creating entity (outer)")
        raise HTTPException(status_code=500, detail="Internal server error creating entity")


@router.get("/", response_model=List[schemas.EntityRead])
def list_entities(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500),
                  q: Optional[str] = None, type: Optional[str] = None,
                  db: Session = Depends(db.get_db)):
    qset = db.query(models.Entity)

    if type:
        try:
            type_enum = schemas.EntityType(type.lower())
            qset = qset.filter(models.Entity.type == type_enum.value)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid entity type '{type}'")

    if q:
        qset = qset.filter(
            (models.Entity.external_id.ilike(f"%{q}%")) |
            (models.Entity.type.ilike(f"%{q}%"))
        )

    return qset.order_by(models.Entity.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{entity_id}", response_model=schemas.EntityRead)
def get_entity(entity_id: UUID, db: Session = Depends(db.get_db)):
    entity = db.query(models.Entity).filter_by(id=entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.get("/external/{external_id}", response_model=schemas.EntityRead)
def get_entity_by_external_id(external_id: str, db: Session = Depends(db.get_db)):
    entity = db.query(models.Entity).filter_by(external_id=external_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity with external_id '{external_id}' not found")
    return entity
