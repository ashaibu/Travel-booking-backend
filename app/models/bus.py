from sqlalchemy import Column, Integer, String, CheckConstraint

from app.database.database import Base


class Bus(Base):
    __tablename__ = "buses"

    __table_args__ = (
        CheckConstraint(
            "price >= 0",
            name="check_bus_price_non_negative"
        ),
        CheckConstraint(
            "available_seats >= 0",
            name="check_bus_seats_non_negative"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    operator = Column(String, nullable=False)
    from_ = Column(String, nullable=False)
    to = Column(String, nullable=False)
    departure = Column(String, nullable=False)
    arrival = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)