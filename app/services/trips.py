"""
PERSON 1 — BACKEND DEVELOPER

One set of trip functions, reused by the flights/buses/ships routers
(each just calls these with mode="flight"/"bus"/"ship" baked in) and
by the admin router. Keeps search/filter/CRUD logic in exactly one place.
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Trip, TripMode
from app.schemas import TripCreateRequest, TripUpdateRequest


def search_trips(
    db: Session,
    mode: TripMode,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    travel_date: Optional[date] = None,
) -> list[Trip]:
    query = db.query(Trip).filter(Trip.mode == mode)
    if origin:
        query = query.filter(Trip.origin.ilike(f"%{origin}%"))
    if destination:
        query = query.filter(Trip.destination.ilike(f"%{destination}%"))
    if travel_date:
        start = datetime.combine(travel_date, datetime.min.time())
        end = datetime.combine(travel_date, datetime.max.time())
        query = query.filter(Trip.departure_time.between(start, end))
    return query.order_by(Trip.departure_time).all()


def get_trip(db: Session, trip_id: int) -> Optional[Trip]:
    return db.get(Trip, trip_id)


def create_trip(db: Session, data: TripCreateRequest) -> Trip:
    trip = Trip(**data.model_dump(), available_seats=data.total_seats)
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def update_trip(db: Session, trip: Trip, data: TripUpdateRequest) -> Trip:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(trip, field, value)
    db.commit()
    db.refresh(trip)
    return trip


def delete_trip(db: Session, trip: Trip) -> None:
    db.delete(trip)
    db.commit()


def reserve_seat(db: Session, trip: Trip) -> None:
    """Called when a booking is created. Raises if sold out."""
    if trip.available_seats <= 0:
        raise ValueError("No seats available on this trip")
    trip.available_seats -= 1
    db.commit()


def release_seat(db: Session, trip: Trip) -> None:
    """Called when a booking is cancelled."""
    trip.available_seats = min(trip.available_seats + 1, trip.total_seats)
    db.commit()
