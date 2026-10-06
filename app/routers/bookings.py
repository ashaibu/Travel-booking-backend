"""
PERSON 3 — BOOKING & PAYMENT DEVELOPER

Seat selection + booking creation + booking reference + cancellation.
A booking starts as "pending_payment" — payments.py flips it to
"confirmed" only after Flutterwave verification succeeds server-side.
"""

import random
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Booking, BookingStatus, User
from app.schemas import BookingCreateRequest, BookingOut
from app.services import trips as trip_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


def generate_booking_ref() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"BK-{suffix}"


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    data: BookingCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trip = trip_service.get_trip(db, data.trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    try:
        trip_service.reserve_seat(db, trip)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    booking = Booking(
        booking_ref=generate_booking_ref(),
        user_id=user.id,
        trip_id=trip.id,
        seat_number=data.seat_number,
        passenger_name=data.passenger_name,
        passenger_phone=data.passenger_phone,
        amount=trip.price,
        status=BookingStatus.pending_payment,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.get("", response_model=list[BookingOut])
def my_bookings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Powers Person 2's "My Tickets" page."""
    return (
        db.query(Booking)
        .filter(Booking.user_id == user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(booking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    booking = db.get(Booking, booking_id)
    if not booking or booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status == BookingStatus.cancelled:
        raise HTTPException(status_code=400, detail="Booking already cancelled")

    was_paid = booking.status == BookingStatus.confirmed
    booking.status = BookingStatus.cancelled
    trip_service.release_seat(db, booking.trip)
    db.commit()
    db.refresh(booking)

    if was_paid:
        # Real refund logic (calling Flutterwave's refund endpoint) goes
        # here — left as a TODO since it needs a live secret key to test.
        pass

    return booking
