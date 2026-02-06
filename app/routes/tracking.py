# app/routes/tracking.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from app import models, schemas, db

router = APIRouter(tags=["Tracking"])


@router.post("/package", response_model=schemas.EntityRead, status_code=201)
def create_package(
        tracking_number: str,
        sender: str,
        recipient: str,
        destination: str,
        weight_kg: Optional[float] = None,
        extra_data: Optional[dict] = None,
        db: Session = Depends(db.get_db)
):
    """
    Create a new package for tracking.

    This is a convenience endpoint that creates an entity of type 'package'.
    """
    # Check if tracking number already exists
    existing = (
        db.query(models.Entity)
        .filter(models.Entity.external_id == tracking_number)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Tracking number {tracking_number} already exists"
        )

    # Prepare package data
    package_data = {
        "sender": sender,
        "recipient": recipient,
        "destination": destination,
    }
    if weight_kg:
        package_data["weight_kg"] = weight_kg
    if extra_data:
        package_data.update(extra_data)

    # Create package entity
    db_package = models.Entity(
        type="package",
        external_id=tracking_number,
        extra_data=package_data
    )

    db.add(db_package)
    try:
        db.commit()
        db.refresh(db_package)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create package: {str(e)}")

    # Create initial "created" event
    db_event = models.Event(
        entity_id=db_package.id,
        event_type="created",
        location=None,
        actor="system",
        payload={"tracking_number": tracking_number}
    )
    db.add(db_event)
    db.commit()

    return db_package


@router.post("/package/{tracking_number}/event", response_model=schemas.EventRead, status_code=201)
def add_package_event(
        tracking_number: str,
        status: schemas.PackageStatus,
        location: Optional[str] = None,
        actor: Optional[str] = None,
        notes: Optional[str] = None,
        extra_data: Optional[dict] = None,
        db: Session = Depends(db.get_db)
):
    """
    Add a status update event to a package.

    Example statuses: picked_up, in_transit, sorting_center,
                      out_for_delivery, delivered, etc.
    """
    # Find package
    package = (
        db.query(models.Entity)
        .filter(
            models.Entity.external_id == tracking_number,
            models.Entity.type == "package"
        )
        .first()
    )

    if not package:
        raise HTTPException(
            status_code=404,
            detail=f"Package with tracking number {tracking_number} not found"
        )

    # Prepare event payload
    payload = {}
    if notes:
        payload["notes"] = notes
    if extra_data:
        payload.update(extra_data)

    # Create event
    db_event = models.Event(
        entity_id=package.id,
        event_type=status.value,
        location=location,
        actor=actor,
        payload=payload if payload else None
    )

    db.add(db_event)
    try:
        db.commit()
        db.refresh(db_event)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add event: {str(e)}")

    return db_event


@router.get("/track/{tracking_number}", response_model=schemas.TrackingResponse)
def track_package(
        tracking_number: str,
        db: Session = Depends(db.get_db)
):
    """
    Track a package by its tracking number.

    Returns the complete timeline of all status updates with timestamps and locations.
    """
    # Find package by external_id (tracking number)
    package = (
        db.query(models.Entity)
        .filter(
            models.Entity.external_id == tracking_number,
            models.Entity.type == "package"
        )
        .first()
    )

    if not package:
        raise HTTPException(
            status_code=404,
            detail=f"Tracking number {tracking_number} not found"
        )

    # Get all events for this package ordered by timestamp
    events = (
        db.query(models.Event)
        .filter(models.Event.entity_id == package.id)
        .order_by(models.Event.timestamp)
        .all()
    )

    # Build response
    return schemas.TrackingResponse(
        tracking_number=tracking_number,
        package=schemas.PackageDetails(
            id=package.id,
            type=package.type,
            details=package.extra_data,
            created_at=package.created_at
        ),
        status=schemas.PackageStatus(events[-1].event_type) if events else schemas.PackageStatus.CREATED,
        current_location=events[-1].location if events else None,
        timeline=[
            schemas.TimelineEvent(
                status=schemas.PackageStatus(event.event_type),
                location=event.location,
                timestamp=event.timestamp,
                actor=event.actor,
                details=event.payload
            )
            for event in events
        ]
    )


@router.get("/packages", response_model=List[dict])
def list_packages(
        status: Optional[schemas.PackageStatus] = None,
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=500),
        db: Session = Depends(db.get_db)
):
    """
    List all packages, optionally filtered by current status.
    """
    # Get all packages
    query = db.query(models.Entity).filter(models.Entity.type == "package")
    packages = query.offset(skip).limit(limit).all()

    result = []
    for package in packages:
        # Get latest event for each package
        latest_event = (
            db.query(models.Event)
            .filter(models.Event.entity_id == package.id)
            .order_by(models.Event.timestamp.desc())
            .first()
        )

        current_status = latest_event.event_type if latest_event else "created"

        # Filter by status if provided
        if status and current_status != status.value:
            continue

        result.append({
            "tracking_number": package.external_id,
            "id": package.id,
            "current_status": current_status,
            "current_location": latest_event.location if latest_event else None,
            "created_at": package.created_at,
            "last_updated": latest_event.timestamp if latest_event else package.created_at,
            "details": package.extra_data
        })

    return result


@router.get("/stats")
def get_tracking_stats(db: Session = Depends(db.get_db)):
    """
    Get statistics about packages in the system.
    """
    from sqlalchemy import func, distinct

    # Total packages
    total_packages = db.query(models.Entity).filter(models.Entity.type == "package").count()

    # Get status distribution
    # This is a bit complex - we need to get the latest event for each package
    subquery = (
        db.query(
            models.Event.entity_id,
            func.max(models.Event.timestamp).label('max_timestamp')
        )
        .group_by(models.Event.entity_id)
        .subquery()
    )

    latest_events = (
        db.query(models.Event.event_type, func.count(models.Event.entity_id))
        .join(
            subquery,
            (models.Event.entity_id == subquery.c.entity_id) &
            (models.Event.timestamp == subquery.c.max_timestamp)
        )
        .group_by(models.Event.event_type)
        .all()
    )

    status_distribution = {status: count for status, count in latest_events}

    return {
        "total_packages": total_packages,
        "status_distribution": status_distribution,
        "total_events": db.query(models.Event).count()
    }