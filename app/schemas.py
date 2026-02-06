# app/schemas.py
from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Dict, Any, List
from datetime import datetime

# ----------------------
# Entity Schemas
# ----------------------
class EntityBase(BaseModel):
    type: str
    external_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

class EntityCreate(EntityBase):
    pass

class EntityUpdate(BaseModel):
    type: Optional[str] = None
    external_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None

class EntityRead(EntityBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------------
# Event Schemas
# ----------------------
class EventBase(BaseModel):
    event_type: str
    location: Optional[str] = None
    actor: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

class EventCreate(EventBase):
    entity_id: UUID

class EventUpdate(BaseModel):
    event_type: Optional[str] = None
    location: Optional[str] = None
    actor: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

class EventRead(EventBase):
    id: UUID
    entity_id: UUID
    timestamp: datetime

    class Config:
        from_attributes = True

# ----------------------
# EntityLink Schemas
# ----------------------
class EntityLinkBase(BaseModel):
    parent_id: UUID
    child_id: UUID
    relation: str

class EntityLinkCreate(EntityLinkBase):
    pass

class EntityLinkRead(EntityLinkBase):
    class Config:
        from_attributes = True
