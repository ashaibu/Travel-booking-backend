from pydantic import BaseModel
from datetime import datetime


class BookingCreate(BaseModel):
    transport_type: str
    transport_id: int


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