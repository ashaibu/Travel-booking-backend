"""
PERSON 1 — BACKEND DEVELOPER — trips.

One table covers flights/buses/ships via `mode`, instead of three
duplicated tables. The flights/buses/ships ROUTERS still exist
separately (that's what Person 2's frontend calls), they just all
read/write this same table underneath — see app/services/trips.py.
"""

import enum

from sqlalchemy import Column, DateTime, Enum, Float, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class TripMode(str, enum.Enum):
    flight = "flight"
    bus = "bus"
    ship = "ship"


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True)
    mode = Column(Enum(TripMode), nullable=False, index=True)
    operator_name = Column(String, nullable=False)
    origin = Column(String, nullable=False, index=True)
    destination = Column(String, nullable=False, index=True)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=True)
    price = Column(Float, nullable=False)  # NGN
    total_seats = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)

    bookings = relationship("Booking", back_populates="trip")
