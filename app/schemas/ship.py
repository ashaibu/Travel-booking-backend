from pydantic import BaseModel, Field


class ShipResponse(BaseModel):
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


class ShipCreate(BaseModel):
    operator: str
    from_: str = Field(alias="from")
    to: str
    departure: str
    arrival: str
    price: int
    available_seats: int

    class Config:
        populate_by_name = True