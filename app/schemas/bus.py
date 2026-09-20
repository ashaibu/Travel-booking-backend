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
    operator: str = Field(min_length=2)
    from_: str = Field(alias="from", min_length=2)
    to: str = Field(min_length=2)
    departure: str = Field(min_length=1)
    arrival: str = Field(min_length=1)
    price: int = Field(gt=0)
    available_seats: int = Field(ge=0)

    class Config:
        populate_by_name = True