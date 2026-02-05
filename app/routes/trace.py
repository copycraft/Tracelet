from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app import models, db

router = APIRouter(tags=["Trace"])

def get_ancestors(db: Session, entity_id: UUID, visited=None):
    if visited is None:
        visited = set()
    if entity_id in visited:
        return []
    visited.add(entity_id)

    parents = db.query(models.EntityLink).filter(models.EntityLink.child_id == entity_id).all()
    result = []
    for p in parents:
        result.append(p.parent_id)
        result.extend(get_ancestors(db, p.parent_id, visited))
    return result

def get_descendants(db: Session, entity_id: UUID, visited=None):
    if visited is None:
        visited = set()
    if entity_id in visited:
        return []
    visited.add(entity_id)

    children = db.query(models.EntityLink).filter(models.EntityLink.parent_id == entity_id).all()
    result = []
    for c in children:
        result.append(c.child_id)
        result.extend(get_descendants(db, c.child_id, visited))
    return result

@router.get("/{entity_id}")
def trace_entity(entity_id: UUID, db: Session = Depends(db.get_db)):
    entity = db.query(models.Entity).filter(models.Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    ancestors = get_ancestors(db, entity_id)
    descendants = get_descendants(db, entity_id)

    return {
        "entity_id": entity_id,
        "ancestors": ancestors,
        "descendants": descendants
    }
