from pydantic import BaseModel, Field


class FlightResponse(BaseModel):
    id: int
    airline: str
    from_: str = Field(alias="from")
    to: str
    departure: str
    arrival: str
    price: int
    available_seats: int

    class Config:
        populate_by_name = True


class FlightCreate(BaseModel):
    airline: str
    from_: str = Field(alias="from")
    to: str
    departure: str
    arrival: str
    price: int
    available_seats: int

    class Config:
        populate_by_name = True