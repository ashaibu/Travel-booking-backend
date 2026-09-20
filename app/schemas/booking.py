from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BookingCreate(BaseModel):
    transport_type: Literal["flight", "bus", "ship"]
    transport_id: int = Field(gt=0)


class BookingResponse(BaseModel):
    id: int
    user_id: int
    transport_type: str
    transport_id: int
    ticket_number: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True