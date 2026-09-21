import secrets

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import update
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database.database import get_db
from app.models.booking import Booking
from app.models.flight import Flight
from app.models.bus import Bus
from app.models.ship import Ship
from app.schemas.booking import BookingCreate, BookingResponse
from app.services.dependencies import get_current_user, get_current_admin


router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.post("", response_model=BookingResponse)
def create_booking(
    booking: BookingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    transport = None

    if booking.transport_type == "flight":
        transport = db.query(Flight).filter(
            Flight.id == booking.transport_id
        ).first()

    elif booking.transport_type == "bus":
        transport = db.query(Bus).filter(
            Bus.id == booking.transport_id
        ).first()

    elif booking.transport_type == "ship":
        transport = db.query(Ship).filter(
            Ship.id == booking.transport_id
        ).first()

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid transport type"
        )

    if not transport:
        raise HTTPException(
            status_code=404,
            detail="Transport not found"
        )

    seat_update = None

    if booking.transport_type == "flight":
        seat_update = update(Flight).where(
            Flight.id == booking.transport_id,
            Flight.available_seats > 0
        ).values(
            available_seats=Flight.available_seats - 1
        )

    elif booking.transport_type == "bus":
        seat_update = update(Bus).where(
            Bus.id == booking.transport_id,
            Bus.available_seats > 0
        ).values(
            available_seats=Bus.available_seats - 1
        )

    elif booking.transport_type == "ship":
        seat_update = update(Ship).where(
            Ship.id == booking.transport_id,
            Ship.available_seats > 0
        ).values(
            available_seats=Ship.available_seats - 1
        )

    result = db.execute(seat_update)

    if result.rowcount == 0:
        raise HTTPException(
            status_code=400,
            detail="No available seats"
        )

    ticket_number = "TKT-" + secrets.token_hex(4).upper()

    new_booking = Booking(
        user_id=current_user.id,
        transport_type=booking.transport_type,
        transport_id=booking.transport_id,
        ticket_number=ticket_number,
        status="confirmed"
    )

    db.add(new_booking)

    try:
        db.commit()
        db.refresh(new_booking)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not create booking"
        )

    return new_booking


@router.get("", response_model=list[BookingResponse])
def get_my_bookings(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    bookings = db.query(Booking).filter(
        Booking.user_id == current_user.id
    ).all()

    return bookings


@router.get("/admin/all", response_model=list[BookingResponse])
def get_all_bookings(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    bookings = db.query(Booking).all()

    return bookings


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == current_user.id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    return booking


@router.delete("/{booking_id}")
def cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == current_user.id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    if booking.status != "confirmed":
        raise HTTPException(
            status_code=400,
            detail=f"Booking cannot be cancelled because its status is '{booking.status}'"
        )

    transport = None

    if booking.transport_type == "flight":
        transport = db.query(Flight).filter(
            Flight.id == booking.transport_id
        ).first()

    elif booking.transport_type == "bus":
        transport = db.query(Bus).filter(
            Bus.id == booking.transport_id
        ).first()

    elif booking.transport_type == "ship":
        transport = db.query(Ship).filter(
            Ship.id == booking.transport_id
        ).first()

    if not transport:
        raise HTTPException(
            status_code=500,
            detail="Transport associated with booking was not found"
        )

    transport.available_seats += 1
    booking.status = "cancelled"

    try:
        db.commit()
        db.refresh(booking)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not cancel booking"
        )

    return {
        "message": "Booking cancelled successfully",
        "booking_id": booking.id,
        "status": booking.status
    }
