from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    CheckConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class Payment(Base):
    __tablename__ = "payments"

    __table_args__ = (
        CheckConstraint(
            "amount >= 0",
            name="check_payment_amount_non_negative"
        ),
    )

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

    payment_link = Column(
    String,
    nullable=True
)

    amount = Column(
        Integer,
        nullable=False
    )

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