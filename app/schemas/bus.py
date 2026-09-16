from pydantic import BaseModel, Field


class BusResponse(BaseModel):
    id: int
    operator: str
    from_: str = Field(alias="from")
    to: str
    departure: str
    arrival: str
    price: int
    available_seats: int

    class Config:
        populate_by_name = True


class BusCreate(BaseModel):
    operator: str
    from_: str = Field(alias="from")
    to: str
    departure: str
    arrival: str
    price: int
    available_seats: int

    class Config:
        populate_by_name = True