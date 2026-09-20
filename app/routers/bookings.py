import secrets 

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

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

    if transport.available_seats <= 0:
        raise HTTPException(
            status_code=400,
            detail="No available seats"
        )

    transport.available_seats -= 1

    ticket_number = "TKT-" + secrets.token_hex(4).upper()

    new_booking = Booking(
        user_id=current_user.id,
        transport_type=booking.transport_type,
        transport_id=booking.transport_id,
        ticket_number=ticket_number,
        status="confirmed"
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

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

    if transport:
        transport.available_seats += 1

    booking.status = "cancelled"

    db.commit()
    db.refresh(booking)

    return {
        "message": "Booking cancelled successfully",
        "booking_id": booking.id,
        "status": booking.status
    }


