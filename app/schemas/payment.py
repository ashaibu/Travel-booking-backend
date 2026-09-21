from pydantic import BaseModel


class PaymentInitializeResponse(BaseModel):
    payment_id: int
    booking_id: int
    tx_ref: str
    amount: int
    currency: str
    payment_link: str
    status: str


class PaymentVerifyRequest(BaseModel):
    transaction_id: int


class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    reference: str
    amount: int
    status: str
    provider: str