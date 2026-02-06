# app/routes/links.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from typing import List
from app import models, schemas, db

router = APIRouter(tags=["Links"])


def would_create_cycle(db: Session, parent_id: UUID, child_id: UUID) -> bool:
    """
    Check if creating a link would create a cycle in the graph.

    Uses BFS to traverse from child to see if we can reach parent.
    """
    if parent_id == child_id:
        return True

    visited = set()
    queue = [child_id]

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)

        if current == parent_id:
            return True

        # Get all children of current node
        children_links = (
            db.query(models.EntityLink.child_id)
            .filter(models.EntityLink.parent_id == current)
            .all()
        )

        for (child,) in children_links:
            if child not in visited:
                queue.append(child)

    return False


@router.post("/", response_model=schemas.EntityLinkRead, status_code=201)
def create_link(
        link: schemas.EntityLinkCreate,
        db: Session = Depends(db.get_db)
):
    """
    Create a parent-child relationship between two entities.

    Examples:
    - Shipment contains Package (shipment is parent, package is child)
    - Package contains Item (package is parent, item is child)

    Prevents:
    - Self-referential links
    - Circular relationships
    - Duplicate links
    """
    # Prevent self-referential links
    if link.parent_id == link.child_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot create self-referential link"
        )

    # Check parent and child exist
    parent = db.query(models.Entity).filter(models.Entity.id == link.parent_id).first()
    child = db.query(models.Entity).filter(models.Entity.id == link.child_id).first()

    if not parent:
        raise HTTPException(status_code=404, detail="Parent entity not found")
    if not child:
        raise HTTPException(status_code=404, detail="Child entity not found")

    # Check for cycles
    if would_create_cycle(db, link.parent_id, link.child_id):
        raise HTTPException(
            status_code=400,
            detail="Creating this link would create a circular relationship"
        )

    # Check if link already exists
    existing_link = (
        db.query(models.EntityLink)
        .filter(
            models.EntityLink.parent_id == link.parent_id,
            models.EntityLink.child_id == link.child_id
        )
        .first()
    )
    if existing_link:
        raise HTTPException(
            status_code=400,
            detail="Link already exists between these entities"
        )

    db_link = models.EntityLink(
        parent_id=link.parent_id,
        child_id=link.child_id,
        relation=link.relation
    )

    db.add(db_link)

    try:
        db.commit()
        db.refresh(db_link)
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
            detail=f"Error creating link: {str(e)}"
        )

    return db_link


@router.get("/{entity_id}/children", response_model=List[schemas.EntityLinkRead])
def get_children(
        entity_id: UUID,
        db: Session = Depends(db.get_db)
):
    """
    Get all child entities linked to this entity.
    """
    # Check entity exists
    entity = db.query(models.Entity).filter(models.Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    links = (
        db.query(models.EntityLink)
        .filter(models.EntityLink.parent_id == entity_id)
        .all()
    )
    return links


@router.get("/{entity_id}/parents", response_model=List[schemas.EntityLinkRead])
def get_parents(
        entity_id: UUID,
        db: Session = Depends(db.get_db)
):
    """
    Get all parent entities linked to this entity.
    """
    # Check entity exists
    entity = db.query(models.Entity).filter(models.Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    links = (
        db.query(models.EntityLink)
        .filter(models.EntityLink.child_id == entity_id)
        .all()
    )
    return links


@router.delete("/")
def delete_link(
        parent_id: UUID,
        child_id: UUID,
        db: Session = Depends(db.get_db)
):
    """
    Delete a link between two entities.
    """
    link = (
        db.query(models.EntityLink)
        .filter(
            models.EntityLink.parent_id == parent_id,
            models.EntityLink.child_id == child_id
        )
        .first()
    )

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    try:
        db.delete(link)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete link: {str(e)}"
        )

    return {
        "status": "deleted",
        "parent_id": str(parent_id),
        "child_id": str(child_id)
    }