# app / routes / links.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app import models, schemas, db

router = APIRouter(tags=["Links"])

def would_create_cycle(db: Session, parent_id: UUID, child_id: UUID) -> bool:
    """Check for cycle using BFS"""
    if parent_id == child_id:
        return True
    visited, queue = set(), [child_id]
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        if current == parent_id:
            return True
        # use scalars() to get raw child_id values
        children_links = db.query(models.EntityLink.child_id).filter(models.EntityLink.parent_id == current).scalars().all()
        for child in children_links:
            if child not in visited:
                queue.append(child)
    return False


@router.post("/", response_model=schemas.EntityLinkRead, status_code=201)
def create_link(link: schemas.EntityLinkCreate, db: Session = Depends(db.get_db)):
    if link.parent_id == link.child_id:
        raise HTTPException(status_code=400, detail="Cannot create self-referential link")
    parent = db.query(models.Entity).filter(models.Entity.id == link.parent_id).first()
    child = db.query(models.Entity).filter(models.Entity.id == link.child_id).first()
    if not parent or not child:
        raise HTTPException(status_code=404, detail="Parent or child entity not found")
    if would_create_cycle(db, link.parent_id, link.child_id):
        raise HTTPException(status_code=400, detail="Circular relationship detected")
    existing_link = db.query(models.EntityLink)\
        .filter(models.EntityLink.parent_id == link.parent_id, models.EntityLink.child_id == link.child_id).first()
    if existing_link:
        raise HTTPException(status_code=400, detail="Link already exists")
    db_link = models.EntityLink(parent_id=link.parent_id, child_id=link.child_id, relation=link.relation)
    try:
        with db.begin():
            db.add(db_link)
        db.refresh(db_link)
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Error creating link: {str(e)}")
    return db_link


@router.get("/{entity_id}/children", response_model=List[schemas.EntityLinkRead])
def get_children(entity_id: UUID, db: Session = Depends(db.get_db)):
    entity = db.query(models.Entity).filter(models.Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return db.query(models.EntityLink).filter(models.EntityLink.parent_id == entity_id).all()


@router.get("/{entity_id}/parents", response_model=List[schemas.EntityLinkRead])
def get_parents(entity_id: UUID, db: Session = Depends(db.get_db)):
    entity = db.query(models.Entity).filter(models.Entity.id == entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return db.query(models.EntityLink).filter(models.EntityLink.child_id == entity_id).all()


@router.delete("/")
def delete_link(parent_id: UUID, child_id: UUID, db: Session = Depends(db.get_db)):
    link = db.query(models.EntityLink).filter(models.EntityLink.parent_id == parent_id,
                                              models.EntityLink.child_id == child_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    try:
        with db.begin():
            db.delete(link)
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to delete link: {str(e)}")
    return {"status": "deleted", "parent_id": str(parent_id), "child_id": str(child_id)}