"""
PERSON 3 — BOOKING & PAYMENT DEVELOPER

Flutterwave integration, same checkout-modal flow as ASAA Travel, but
with one important upgrade: /payments/verify does NOT just trust the
browser's callback. It calls Flutterwave's own verify endpoint
server-side with the SECRET key and checks the amount/currency/status
itself before confirming the booking. This is what ASAA Travel's
simpler flow skips — worth doing properly on a team project.
"""

import os
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Booking, BookingStatus, Payment, User
from app.schemas import (
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    PaymentVerifyRequest,
    PaymentVerifyResponse,
)

router = APIRouter(prefix="/payments", tags=["payments"])

FLUTTERWAVE_PUBLIC_KEY = os.environ.get("FLUTTERWAVE_PUBLIC_KEY", "FLWPUBK_TEST-YOUR_PUBLIC_KEY_HERE-X")
FLUTTERWAVE_SECRET_KEY = os.environ.get("FLUTTERWAVE_SECRET_KEY", "FLWSECK_TEST-YOUR_SECRET_KEY_HERE-X")
FLUTTERWAVE_VERIFY_URL = "https://api.flutterwave.com/v3/transactions/{id}/verify"


@router.post("/initiate", response_model=PaymentInitiateResponse)
def initiate_payment(
    data: PaymentInitiateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.get(Booking, data.booking_id)
    if not booking or booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != BookingStatus.pending_payment:
        raise HTTPException(status_code=400, detail="Booking is not awaiting payment")

    tx_ref = f"TGP-{booking.booking_ref}-{booking.id}"

    # Upsert the payment row for this booking (one per booking).
    payment = booking.payment
    if payment is None:
        payment = Payment(booking_id=booking.id, tx_ref=tx_ref, amount=booking.amount)
        db.add(payment)
    else:
        payment.tx_ref = tx_ref
        payment.amount = booking.amount
    db.commit()

    return PaymentInitiateResponse(
        public_key=FLUTTERWAVE_PUBLIC_KEY, tx_ref=tx_ref, amount=booking.amount
    )


@router.post("/verify", response_model=PaymentVerifyResponse)
def verify_payment(
    data: PaymentVerifyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.get(Booking, data.booking_id)
    if not booking or booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Booking not found")

    payment = booking.payment
    if not payment or payment.tx_ref != data.tx_ref:
        raise HTTPException(status_code=400, detail="Payment reference mismatch")

    # --- The part ASAA Travel's simple flow skips: verify with Flutterwave
    # directly, server-side, using the SECRET key. Never trust the
    # browser's callback alone — it can be spoofed. ---
    try:
        resp = httpx.get(
            FLUTTERWAVE_VERIFY_URL.format(id=data.transaction_id),
            headers={"Authorization": f"Bearer {FLUTTERWAVE_SECRET_KEY}"},
            timeout=15.0,
        )
        resp.raise_for_status()
        result = resp.json().get("data", {})
    except httpx.HTTPError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Could not reach Flutterwave: {e}")

    flw_status = result.get("status")
    flw_amount = result.get("amount")
    flw_currency = result.get("currency")

    if (
        flw_status != "successful"
        or flw_currency != "NGN"
        or flw_amount is None
        or float(flw_amount) < float(payment.amount)
    ):
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Payment could not be verified")

    payment.verified = True
    payment.flw_transaction_id = str(data.transaction_id)
    payment.verified_at = datetime.now(timezone.utc)
    booking.status = BookingStatus.confirmed
    db.commit()
    db.refresh(booking)

    return PaymentVerifyResponse(status="success", booking=booking)
