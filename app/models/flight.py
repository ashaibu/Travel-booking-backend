from sqlalchemy import Column, Integer, String, CheckConstraint

from app.database.database import Base


class Flight(Base):
    __tablename__ = "flights"

    __table_args__ = (
        CheckConstraint("price >= 0", name="check_flight_price_non_negative"),
        CheckConstraint(
            "available_seats >= 0",
            name="check_flight_seats_non_negative"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    airline = Column(String, nullable=False)
    from_ = Column(String, nullable=False)
    to = Column(String, nullable=False)
    departure = Column(String, nullable=False)
    arrival = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)
