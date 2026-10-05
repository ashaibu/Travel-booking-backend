"""
PERSON 1 — BACKEND DEVELOPER

Pydantic schemas: what goes IN to each endpoint (validated request bodies)
and what comes OUT (response shapes). Keeps the frontend contract explicit.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models import BookingStatus, TripMode


# ---- Auth / Users ----------------------------------------------------
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_admin: bool


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    is_admin: bool

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None


# ---- Trips -------------------------------------------------------------
class TripOut(BaseModel):
    id: int
    mode: TripMode
    operator_name: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: Optional[datetime]
    price: float
    total_seats: int
    available_seats: int

    class Config:
        from_attributes = True


class TripCreateRequest(BaseModel):
    mode: TripMode
    operator_name: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: Optional[datetime] = None
    price: float
    total_seats: int


class TripUpdateRequest(BaseModel):
    operator_name: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    price: Optional[float] = None
    total_seats: Optional[int] = None


# ---- Bookings ------------------------------------------------------------
class BookingCreateRequest(BaseModel):
    trip_id: int
    seat_number: str
    passenger_name: str
    passenger_phone: str


class BookingOut(BaseModel):
    id: int
    booking_ref: str
    trip_id: int
    seat_number: str
    passenger_name: str
    passenger_phone: str
    amount: float
    status: BookingStatus
    created_at: datetime
    trip: TripOut

    class Config:
        from_attributes = True


# ---- Payments ----------------------------------------------------------
class PaymentInitiateRequest(BaseModel):
    booking_id: int


class PaymentInitiateResponse(BaseModel):
    public_key: str
    tx_ref: str
    amount: float
    currency: str = "NGN"


class PaymentVerifyRequest(BaseModel):
    booking_id: int
    tx_ref: str
    transaction_id: str


class PaymentVerifyResponse(BaseModel):
    status: str
    booking: BookingOut
