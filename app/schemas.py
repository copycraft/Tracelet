# app/schemas.py
from pydantic import BaseModel
from uuid import UUID
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


# ----------------------
# Enums
# ----------------------
class PackageStatus(str, Enum):
    CREATED = "created"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    SORTING_CENTER = "sorting_center"
    CUSTOMS = "customs"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED_DELIVERY = "failed_delivery"
    RETURNED = "returned"
    EXCEPTION = "exception"  # For issues like damaged package, etc.


class EntityType(str, Enum):
    PACKAGE = "package"
    SHIPMENT = "shipment"
    ITEM = "item"
    CONTAINER = "container"


# ----------------------
# Entity Schemas
# ----------------------
class EntityBase(BaseModel):
    type: EntityType
    external_id: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class EntityCreate(EntityBase):
    external_id: str  # Make required for tracking numbers


class EntityUpdate(BaseModel):
    type: Optional[EntityType] = None
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
    event_type: PackageStatus
    location: Optional[str] = None
    actor: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class EventCreate(EventBase):
    entity_id: UUID


class EventUpdate(BaseModel):
    event_type: Optional[PackageStatus] = None
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


# ----------------------
# Tracking Schemas (convenience schemas for the tracking endpoint)
# ----------------------
class PackageDetails(BaseModel):
    id: UUID
    type: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime


class TimelineEvent(BaseModel):
    status: PackageStatus
    location: Optional[str]
    timestamp: datetime
    actor: Optional[str]
    details: Optional[Dict[str, Any]]


class TrackingResponse(BaseModel):
    tracking_number: str
    package: PackageDetails
    status: PackageStatus
    current_location: Optional[str]
    timeline: List[TimelineEvent]