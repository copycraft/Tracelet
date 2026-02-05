from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app import models, schemas, db

router = APIRouter(tags=["Links"])

@router.post("/", response_model=schemas.EntityLinkRead)
def create_link(link: schemas.EntityLinkCreate, db: Session = Depends(db.get_db)):
    # Check parent and child exist
    parent = db.query(models.Entity).filter(models.Entity.id == link.parent_id).first()
    child = db.query(models.Entity).filter(models.Entity.id == link.child_id).first()
    if not parent or not child:
        raise HTTPException(status_code=404, detail="Parent or child entity not found")

    db_link = models.EntityLink(
        parent_id=link.parent_id,
        child_id=link.child_id,
        relation=link.relation
    )
    db.add(db_link)
    try:
        db.commit()
        db.refresh(db_link)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating link: {str(e)}")
    return db_link

@router.get("/{entity_id}/children", response_model=list[schemas.EntityLinkRead])
def get_children(entity_id: UUID, db: Session = Depends(db.get_db)):
    links = db.query(models.EntityLink).filter(models.EntityLink.parent_id == entity_id).all()
    return links

@router.get("/{entity_id}/parents", response_model=list[schemas.EntityLinkRead])
def get_parents(entity_id: UUID, db: Session = Depends(db.get_db)):
    links = db.query(models.EntityLink).filter(models.EntityLink.child_id == entity_id).all()
    return links
