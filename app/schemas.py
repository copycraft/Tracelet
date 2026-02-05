from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from uuid import UUID

class EntityBase(BaseModel):
    type: str
    external_id: str
    extra_data: Optional[Dict[str, Any]] = None

class EntityCreate(EntityBase):
    pass

class EntityRead(EntityBase):
    id: UUID
    created_at: datetime

    class Config:
        orm_mode = True

class EventBase(BaseModel):
    event_type: str
    location: Optional[str] = None
    actor: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

class EventCreate(EventBase):
    entity_id: UUID

class EventRead(EventBase):
    id: UUID
    entity_id: UUID
    timestamp: datetime

    class Config:
        orm_mode = True

class EntityLinkBase(BaseModel):
    parent_id: UUID
    child_id: UUID
    relation: str

class EntityLinkCreate(EntityLinkBase):
    pass

class EntityLinkRead(EntityLinkBase):
    class Config:
        orm_mode = True
