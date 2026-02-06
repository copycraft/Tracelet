# app/routes/entities.py
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

    The external_id must be unique across all entities.
    """
    # Check if external_id already exists
    existing = (
        db.query(models.Entity)
        .filter(models.Entity.external_id == entity.external_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Entity with external_id '{entity.external_id}' already exists"
        )

    db_entity = models.Entity(
        type=entity.type.value,
        external_id=entity.external_id,
        extra_data=entity.extra_data,
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
        type: Optional[schemas.EntityType] = None,
        db: Session = Depends(db.get_db)
):
    """
    List entities with pagination and optional filtering.

    - **q**: Search by external_id or type (case-insensitive)
    - **type**: Filter by entity type (package, shipment, item, container)
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    qset = db.query(models.Entity)

    # Filter by type if provided
    if type:
        qset = qset.filter(models.Entity.type == type.value)

    # Search filter
    if q:
        qset = qset.filter(
            (models.Entity.external_id.ilike(f"%{q}%")) |
            (models.Entity.type.ilike(f"%{q}%"))
        )

    entities = qset.order_by(models.Entity.created_at.desc()).offset(skip).limit(limit).all()
    return entities


@router.get("/{entity_id}", response_model=schemas.EntityRead)
def get_entity(
        entity_id: UUID,
        db: Session = Depends(db.get_db)
):
    """
    Get a specific entity by its UUID.
    """
    entity = db.query(models.Entity).filter_by(id=entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.get("/external/{external_id}", response_model=schemas.EntityRead)
def get_entity_by_external_id(
        external_id: str,
        db: Session = Depends(db.get_db)
):
    """
    Get an entity by its external_id (e.g., tracking number).
    """
    entity = db.query(models.Entity).filter_by(external_id=external_id).first()
    if not entity:
        raise HTTPException(
            status_code=404,
            detail=f"Entity with external_id '{external_id}' not found"
        )
    return entity


@router.patch("/{entity_id}", response_model=schemas.EntityRead)
def update_entity(
        entity_id: UUID,
        update: schemas.EntityUpdate,
        db: Session = Depends(db.get_db)
):
    """
    Update an entity's fields (type, external_id, or extra_data).
    """
    entity = db.query(models.Entity).filter_by(id=entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Update only provided fields
    if update.type is not None:
        entity.type = update.type.value

    if update.external_id is not None:
        # Check for uniqueness if changing external_id
        if update.external_id != entity.external_id:
            existing = (
                db.query(models.Entity)
                .filter(models.Entity.external_id == update.external_id)
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Entity with external_id '{update.external_id}' already exists"
                )
        entity.external_id = update.external_id

    if update.extra_data is not None:
        entity.extra_data = update.extra_data

    try:
        db.commit()
        db.refresh(entity)
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
            detail=f"Error updating entity: {str(e)}"
        )

    return entity


@router.delete("/{entity_id}")
def delete_entity(
        entity_id: UUID,
        force: bool = Query(False, description="Force delete even if entity has links or events"),
        db: Session = Depends(db.get_db)
):
    """
    Delete an entity.

    By default, prevents deletion if the entity has:
    - Links to other entities
    - Associated events

    Use ?force=true to delete anyway (will cascade delete links and events).
    """
    entity = db.query(models.Entity).filter_by(id=entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    if not force:
        # Check for links
        has_links = db.query(models.EntityLink).filter(
            (models.EntityLink.parent_id == entity_id) |
            (models.EntityLink.child_id == entity_id)
        ).first()
        if has_links:
            raise HTTPException(
                status_code=400,
                detail="Entity has links. Use ?force=true to delete."
            )

        # Check for events
        has_events = db.query(models.Event).filter(
            models.Event.entity_id == entity_id
        ).first()
        if has_events:
            raise HTTPException(
                status_code=400,
                detail="Entity has events. Use ?force=true to delete."
            )

    try:
        db.delete(entity)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete entity: {str(e)}"
        )

    return {
        "status": "deleted",
        "entity_id": str(entity_id),
        "external_id": entity.external_id
    }