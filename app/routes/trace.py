from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app import models, db

router = APIRouter(tags=["Trace"])

def get_ancestors(db: Session, entity_id: UUID, visited: set):
    if entity_id in visited:
        return []
    visited.add(entity_id)

    links = (
        db.query(models.EntityLink)
        .filter(models.EntityLink.child_id == entity_id)
        .all()
    )

    result = []
    for link in links:
        parent = db.query(models.Entity).get(link.parent_id)
        if parent:
            result.append(parent)
            result.extend(get_ancestors(db, parent.id, visited))
    return result


def get_descendants(db: Session, entity_id: UUID, visited: set):
    if entity_id in visited:
        return []
    visited.add(entity_id)

    links = (
        db.query(models.EntityLink)
        .filter(models.EntityLink.parent_id == entity_id)
        .all()
    )

    result = []
    for link in links:
        child = db.query(models.Entity).get(link.child_id)
        if child:
            result.append(child)
            result.extend(get_descendants(db, child.id, visited))
    return result


@router.get("/{entity_id}")
def trace_entity(
    entity_id: UUID,
    direction: str = Query("both", enum=["up", "down", "both"]),
    db: Session = Depends(db.get_db)
):
    entity = db.query(models.Entity).filter_by(id=entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    visited = set()
    ancestors = []
    descendants = []

    if direction in ("up", "both"):
        ancestors = get_ancestors(db, entity_id, visited)

    if direction in ("down", "both"):
        descendants = get_descendants(db, entity_id, visited)

    return {
        "entity": entity,
        "ancestors": ancestors,
        "descendants": descendants,
    }
