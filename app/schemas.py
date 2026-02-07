from pydantic import BaseModel, Field, root_validator
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
    EXCEPTION = "exception"


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
    extra_data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"  # allow name, id, scanner junk


class EntityCreate(BaseModel):
    type: EntityType
    external_id: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"

    @root_validator(pre=True)
    def set_external_id(cls, values):
        if not values.get("external_id") and values.get("id"):
            values["external_id"] = values["id"]
        if not values.get("external_id"):
            raise ValueError("external_id or id is required")
        if values.get("name"):
            values.setdefault("extra_data", {})
            values["extra_data"]["name"] = values.pop("name")
        return values



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
# Tracking Schemas
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
