"""PERSON 1 — BACKEND DEVELOPER — flights (mode="flight" over the shared Trip table)."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TripMode
from app.schemas import TripOut
from app.services import trips as trip_service

router = APIRouter(prefix="/flights", tags=["flights"])


@router.get("", response_model=list[TripOut])
def list_flights(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    travel_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    return trip_service.search_trips(db, TripMode.flight, origin, destination, travel_date)


@router.get("/{flight_id}", response_model=TripOut)
def get_flight(flight_id: int, db: Session = Depends(get_db)):
    trip = trip_service.get_trip(db, flight_id)
    if not trip or trip.mode != TripMode.flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    return trip
