"""PERSON 1 — BACKEND DEVELOPER — ships (mode="ship" over the shared Trip table)."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TripMode
from app.schemas import TripOut
from app.services import trips as trip_service

router = APIRouter(prefix="/ships", tags=["ships"])


@router.get("", response_model=list[TripOut])
def list_ships(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    travel_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    return trip_service.search_trips(db, TripMode.ship, origin, destination, travel_date)


@router.get("/{ship_id}", response_model=TripOut)
def get_ship(ship_id: int, db: Session = Depends(get_db)):
    trip = trip_service.get_trip(db, ship_id)
    if not trip or trip.mode != TripMode.ship:
        raise HTTPException(status_code=404, detail="Ship not found")
    return trip
