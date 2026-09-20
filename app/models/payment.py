from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    booking_id = Column(
        Integer,
        ForeignKey("bookings.id"),
        nullable=False
    )

    reference = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    amount = Column(Integer, nullable=False)

    status = Column(
        String,
        nullable=False,
        default="pending"
    )

    provider = Column(
        String,
        nullable=False,
        default="paystack"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    booking = relationship("Booking")