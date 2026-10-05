"""PERSON 1 — BACKEND DEVELOPER — buses (mode="bus" over the shared Trip table)."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TripMode
from app.schemas import TripOut
from app.services import trips as trip_service

router = APIRouter(prefix="/buses", tags=["buses"])


@router.get("", response_model=list[TripOut])
def list_buses(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    travel_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    return trip_service.search_trips(db, TripMode.bus, origin, destination, travel_date)


@router.get("/{bus_id}", response_model=TripOut)
def get_bus(bus_id: int, db: Session = Depends(get_db)):
    trip = trip_service.get_trip(db, bus_id)
    if not trip or trip.mode != TripMode.bus:
        raise HTTPException(status_code=404, detail="Bus not found")
    return trip
