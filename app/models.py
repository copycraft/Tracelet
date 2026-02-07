# app / models
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base


def utc_now():
    """Helper function to get current UTC time."""
    return datetime.now(timezone.utc)


class Entity(Base):
    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String, nullable=False, index=True)
    external_id = Column(String, unique=True, nullable=False, index=True)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    # Relationships
    events = relationship(
        "Event",
        back_populates="entity",
        cascade="all, delete-orphan"
    )
    children = relationship(
        "EntityLink",
        foreign_keys="EntityLink.parent_id",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    parents = relationship(
        "EntityLink",
        foreign_keys="EntityLink.child_id",
        back_populates="child",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Entity(id={self.id}, type={self.type}, external_id={self.external_id})>"


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    location = Column(String, nullable=True)
    actor = Column(String, nullable=True)
    payload = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, index=True)

    # Relationship
    entity = relationship("Entity", back_populates="events")

    def __repr__(self):
        return f"<Event(id={self.id}, type={self.event_type}, entity_id={self.entity_id})>"


class EntityLink(Base):
    __tablename__ = "entity_links"

    parent_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), primary_key=True)
    child_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), primary_key=True)
    relation = Column(String, nullable=False)

    # Relationships
    parent = relationship("Entity", foreign_keys=[parent_id], back_populates="children")
    child = relationship("Entity", foreign_keys=[child_id], back_populates="parents")

    def __repr__(self):
        return f"<EntityLink(parent={self.parent_id}, child={self.child_id}, relation={self.relation})>"

    # Add index for faster lookups
    __table_args__ = (
        Index('idx_parent_child', 'parent_id', 'child_id'),
    )