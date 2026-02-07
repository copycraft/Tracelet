from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from typing import List, Optional
from app import models, schemas, db

router = APIRouter(tags=["Entities"])


@router.post("/", response_model=schemas.EntityRead, status_code=201)
def create_entity(
    entity: schemas.EntityCreate,
    db: Session = Depends(db.get_db)
):
    """
    Create a new entity (package, shipment, item, or container).
    """

    # Ensure entity type is valid Enum
    if isinstance(entity.type, str):
        try:
            entity.type = schemas.EntityType(entity.type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid entity type '{entity.type}'")

    # Check if external_id already exists
    existing = db.query(models.Entity).filter(models.Entity.external_id == entity.external_id).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Entity with external_id '{entity.external_id}' already exists"
        )

    db_entity = models.Entity(
        type=entity.type.value,         # Enum value stored in DB
        external_id=entity.external_id,
        extra_data=entity.extra_data or {},  # Ensure extra_data is dict
    )

    db.add(db_entity)

    try:
        db.commit()
        db.refresh(db_entity)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Database constraint violation: {str(e.orig)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating entity: {str(e)}"
        )

    return db_entity


@router.get("/", response_model=List[schemas.EntityRead])
def list_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: Optional[str] = None,
    type: Optional[str] = None,  # Accept string from query
    db: Session = Depends(db.get_db)
):
    qset = db.query(models.Entity)

    # Convert type string to Enum if provided
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
