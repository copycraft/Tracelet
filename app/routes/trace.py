# app / routes / trace

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import List
from app import models, schemas, db

router = APIRouter(tags=["Trace"])


def get_ancestors(
        db: Session,
        entity_id: UUID,
        visited: set,
        max_depth: int = 10,
        current_depth: int = 0
) -> List[models.Entity]:
    """Recursively get all parent entities"""
    if entity_id in visited or current_depth >= max_depth:
        return []
    visited.add(entity_id)

    # Use joinedload to avoid N+1 queries
    links = (
        db.query(models.EntityLink)
        .options(joinedload(models.EntityLink.parent))
        .filter(models.EntityLink.child_id == entity_id)
        .all()
    )

    result = []
    for link in links:
        if link.parent:
            result.append(link.parent)
            result.extend(
                get_ancestors(db, link.parent.id, visited, max_depth, current_depth + 1)
            )
    return result


def get_descendants(
        db: Session,
        entity_id: UUID,
        visited: set,
        max_depth: int = 10,
        current_depth: int = 0
) -> List[models.Entity]:
    """Recursively get all child entities"""
    if entity_id in visited or current_depth >= max_depth:
        return []
    visited.add(entity_id)

    # Use joinedload to avoid N+1 queries
    links = (
        db.query(models.EntityLink)
        .options(joinedload(models.EntityLink.child))
        .filter(models.EntityLink.parent_id == entity_id)
        .all()
    )

    result = []
    for link in links:
        if link.child:
            result.append(link.child)
            result.extend(
                get_descendants(db, link.child.id, visited, max_depth, current_depth + 1)
            )
    return result


@router.get("/{entity_id}")
def trace_entity(
        entity_id: UUID,
        direction: str = Query("both", enum=["up", "down", "both"]),
        max_depth: int = Query(10, ge=1, le=50, description="Maximum depth to traverse"),
        db: Session = Depends(db.get_db)
):
    """
    Trace entity relationships (parent-child hierarchy).

    - **up**: Get all ancestors (parents, grandparents, etc.)
    - **down**: Get all descendants (children, grandchildren, etc.)
    - **both**: Get both ancestors and descendants

    Example use cases:
    - Find all packages in a shipment (direction=down)
    - Find which container a package belongs to (direction=up)
    """
    entity = db.query(models.Entity).filter_by(id=entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    visited = set()
    ancestors = []
    descendants = []

    if direction in ("up", "both"):
        ancestors = get_ancestors(db, entity_id, visited, max_depth)

    if direction in ("down", "both"):
        # Reset visited set for descendants if we did both
        if direction == "both":
            visited = set()
        descendants = get_descendants(db, entity_id, visited, max_depth)

    return {
        "entity": {
            "id": entity.id,
            "type": entity.type,
            "external_id": entity.external_id,
            "extra_data": entity.extra_data,
            "created_at": entity.created_at
        },
        "ancestors": [
            {
                "id": e.id,
                "type": e.type,
                "external_id": e.external_id,
                "extra_data": e.extra_data
            }
            for e in ancestors
        ],
        "descendants": [
            {
                "id": e.id,
                "type": e.type,
                "external_id": e.external_id,
                "extra_data": e.extra_data
            }
            for e in descendants
        ],
        "count": {
            "ancestors": len(ancestors),
            "descendants": len(descendants)
        }
    }


@router.get("/{entity_id}/tree")
def get_entity_tree(
        entity_id: UUID,
        db: Session = Depends(db.get_db)
):
    """
    Get the full entity tree showing parent-child relationships.
    Useful for visualizing shipment > package > item hierarchies.
    """
    entity = db.query(models.Entity).filter_by(id=entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Get all links where this entity is involved
    parent_links = (
        db.query(models.EntityLink)
        .options(joinedload(models.EntityLink.parent))
        .filter(models.EntityLink.child_id == entity_id)
        .all()
    )

    child_links = (
        db.query(models.EntityLink)
        .options(joinedload(models.EntityLink.child))
        .filter(models.EntityLink.parent_id == entity_id)
        .all()
    )

    return {
        "entity": {
            "id": entity.id,
            "type": entity.type,
            "external_id": entity.external_id,
            "extra_data": entity.extra_data
        },
        "parents": [
            {
                "id": link.parent.id,
                "type": link.parent.type,
                "external_id": link.parent.external_id,
                "relation": link.relation
            }
            for link in parent_links
        ],
        "children": [
            {
                "id": link.child.id,
                "type": link.child.type,
                "external_id": link.child.external_id,
                "relation": link.relation
            }
            for link in child_links
        ]
    }