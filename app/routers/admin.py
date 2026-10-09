"""
PERSON 4 — UI/UX + TESTING + ADMIN

Not in the original folder sketch, but the admin dashboard (add/edit/
delete trips, view bookings & payments, manage seats) needs something
to call — this is that backend surface. Every route here requires
get_current_admin.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_admin
from app.database import get_db
from app.models import Booking, Payment, Trip, User
from app.schemas import BookingOut, TripCreateRequest, TripOut, TripUpdateRequest, UserOut
from app.services import trips as trip_service

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


# ---- Trips ---------------------------------------------------------------
@router.get("/trips", response_model=list[TripOut])
def list_all_trips(db: Session = Depends(get_db)):
    return db.query(Trip).order_by(Trip.departure_time).all()


@router.post("/trips", response_model=TripOut, status_code=201)
def create_trip(data: TripCreateRequest, db: Session = Depends(get_db)):
    return trip_service.create_trip(db, data)


@router.put("/trips/{trip_id}", response_model=TripOut)
def update_trip(trip_id: int, data: TripUpdateRequest, db: Session = Depends(get_db)):
    trip = trip_service.get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip_service.update_trip(db, trip, data)


@router.delete("/trips/{trip_id}", status_code=204)
def delete_trip(trip_id: int, db: Session = Depends(get_db)):
    trip = trip_service.get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    trip_service.delete_trip(db, trip)


# ---- Bookings & payments (read-only oversight) ---------------------------
@router.get("/bookings", response_model=list[BookingOut])
def list_all_bookings(db: Session = Depends(get_db)):
    return db.query(Booking).order_by(Booking.created_at.desc()).all()


@router.get("/payments")
def list_all_payments(db: Session = Depends(get_db)):
    payments = db.query(Payment).order_by(Payment.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "booking_id": p.booking_id,
            "tx_ref": p.tx_ref,
            "amount": p.amount,
            "verified": p.verified,
            "created_at": p.created_at,
        }
        for p in payments
    ]


# ---- Users -----------------------------------------------------------
@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()
