from sqlalchemy import Column, Integer, String

from app.database.database import Base


class Ship(Base):
    __tablename__ = "ships"

    id = Column(Integer, primary_key=True, index=True)
    operator = Column(String, nullable=False)
    from_ = Column(String, nullable=False)
    to = Column(String, nullable=False)
    departure = Column(String, nullable=False)
    arrival = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)