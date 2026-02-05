# app/models.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base

class Entity(Base):
    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String, nullable=False)
    external_id = Column(String, unique=True, nullable=False)
    # Avoid reserved name 'metadata' in SQLAlchemy models
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    events = relationship("Event", back_populates="entity", cascade="all, delete-orphan")
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

class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False)
    event_type = Column(String, nullable=False)
    location = Column(String, nullable=True)
    actor = Column(String, nullable=True)
    payload = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    entity = relationship("Entity", back_populates="events")

class EntityLink(Base):
    __tablename__ = "entity_links"

    parent_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), primary_key=True)
    child_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), primary_key=True)
    relation = Column(String, nullable=False)

    parent = relationship("Entity", foreign_keys=[parent_id], back_populates="children")
    child = relationship("Entity", foreign_keys=[child_id], back_populates="parents")
