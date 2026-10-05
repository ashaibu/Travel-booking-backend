"""
PERSON 1 — BACKEND DEVELOPER

Split into one file per entity for readability. This __init__ re-exports
everything so the rest of the app can still do `from app.models import User`
without caring which file it actually lives in.
"""

from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment
from app.models.trip import Trip, TripMode
from app.models.user import User

__all__ = ["User", "Trip", "TripMode", "Booking", "BookingStatus", "Payment"]
