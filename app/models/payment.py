"""PERSON 3 — BOOKING & PAYMENT DEVELOPER — payment records (one per booking)."""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), unique=True, nullable=False)
    tx_ref = Column(String, unique=True, index=True, nullable=False)
    flw_transaction_id = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    verified_at = Column(DateTime(timezone=True), nullable=True)

    booking = relationship("Booking", back_populates="payment")
