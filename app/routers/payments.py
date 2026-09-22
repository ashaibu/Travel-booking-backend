import secrets
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.booking import Booking
from app.models.payment import Payment
from app.schemas.payment import (
    PaymentInitializeResponse,
    PaymentVerifyRequest,
    PaymentResponse,
)
from app.services.dependencies import get_current_user
from app.services.flutterwave import (
    FLW_SECRET_HASH,
    initialize_payment,
    verify_transaction,
)


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post("/webhook")
async def flutterwave_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Receive and securely process Flutterwave webhook events.
    """

    # 1. Make sure the webhook secret is configured
    if not FLW_SECRET_HASH:
        raise HTTPException(
            status_code=500,
            detail="Flutterwave webhook secret is not configured",
        )

    # 2. Flutterwave sends the configured secret hash
    #    in the verif-hash header.
    signature = request.headers.get("verif-hash")

    if not signature:
        raise HTTPException(
            status_code=401,
            detail="Missing Flutterwave signature",
        )

    # 3. Compare the received hash with our secret hash.
    if signature != FLW_SECRET_HASH:
        raise HTTPException(
            status_code=401,
            detail="Invalid Flutterwave signature",
        )

    # 4. Read the webhook body
    body = await request.body()

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook payload",
        )

    # 5. Get transaction data
    transaction_data = payload.get("data", {})

    transaction_id = transaction_data.get("id")
    tx_ref = transaction_data.get("tx_ref")

    if not transaction_id:
        raise HTTPException(
            status_code=400,
            detail="Transaction ID missing from webhook",
        )

    if not tx_ref:
        raise HTTPException(
            status_code=400,
            detail="Transaction reference missing from webhook",
        )

    # 6. Find our payment using Flutterwave's transaction reference
    payment = (
        db.query(Payment)
        .filter(Payment.reference == tx_ref)
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment record not found",
        )

    # 7. Idempotency:
    #    If this webhook has already successfully paid the
    #    payment, don't process it again.
    if payment.status == "paid":
        return {
            "message": "Payment already processed",
            "payment_id": payment.id,
            "reference": payment.reference,
            "status": payment.status,
        }

    # 8. NEVER trust the webhook payload alone.
    #    Verify the transaction directly with Flutterwave.
    transaction = verify_transaction(transaction_id)

    verified_data = transaction.get(
        "data",
        {},
    )

    verified_tx_ref = verified_data.get("tx_ref")
    verified_amount = verified_data.get("amount")
    verified_currency = verified_data.get("currency")
    verified_status = verified_data.get("status")

    # 9. Make sure the verified reference matches our payment
    if verified_tx_ref != payment.reference:
        raise HTTPException(
            status_code=400,
            detail="Transaction reference does not match payment",
        )

    # 10. Make sure the amount matches
    if verified_amount != payment.amount:
        raise HTTPException(
            status_code=400,
            detail="Payment amount does not match booking amount",
        )

    # 11. Make sure the currency matches
    if verified_currency != "NGN":
        raise HTTPException(
            status_code=400,
            detail="Payment currency does not match expected currency",
        )

    # 12. Handle unsuccessful payment
    if verified_status != "successful":
        payment.status = "failed"

        db.commit()

        return {
            "message": "Payment was not successful",
            "payment_id": payment.id,
            "reference": payment.reference,
            "status": payment.status,
        }

    # 13. Payment is genuinely successful
    payment.status = "paid"

    db.commit()
    db.refresh(payment)

    return {
        "message": "Payment processed successfully",
        "payment_id": payment.id,
        "booking_id": payment.booking_id,
        "reference": payment.reference,
        "amount": payment.amount,
        "currency": verified_currency,
        "status": payment.status,
    }


@router.post(
    "/{booking_id}/initialize",
    response_model=PaymentInitializeResponse,
)
def initialize_booking_payment(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == current_user.id,
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    if booking.status != "confirmed":
        raise HTTPException(
            status_code=400,
            detail="Only confirmed bookings can be paid for",
        )

    # Check if the booking has already been paid
    existing_payment = db.query(Payment).filter(
        Payment.booking_id == booking.id,
        Payment.status == "paid",
    ).first()

    if existing_payment:
        raise HTTPException(
            status_code=400,
            detail="Booking has already been paid for",
        )

    # Reuse an existing pending payment that has a payment link
    pending_payment = db.query(Payment).filter(
        Payment.booking_id == booking.id,
        Payment.status == "pending",
        Payment.payment_link.isnot(None),
    ).order_by(Payment.id.desc()).first()

    if pending_payment:
        return {
            "payment_id": pending_payment.id,
            "booking_id": booking.id,
            "tx_ref": pending_payment.reference,
            "amount": pending_payment.amount,
            "currency": "NGN",
            "payment_link": pending_payment.payment_link,
            "status": pending_payment.status,
        }

    # Find the transport connected to the booking
    transport = None

    if booking.transport_type == "flight":
        from app.models.flight import Flight

        transport = db.query(Flight).filter(
            Flight.id == booking.transport_id
        ).first()

    elif booking.transport_type == "bus":
        from app.models.bus import Bus

        transport = db.query(Bus).filter(
            Bus.id == booking.transport_id
        ).first()

    elif booking.transport_type == "ship":
        from app.models.ship import Ship

        transport = db.query(Ship).filter(
            Ship.id == booking.transport_id
        ).first()

    if not transport:
        raise HTTPException(
            status_code=404,
            detail="Transport not found",
        )

    amount = transport.price
    currency = "NGN"

    # Generate a unique Flutterwave transaction reference
    tx_ref = (
        f"TRAVEL-{booking.id}-"
        f"{secrets.token_hex(8).upper()}"
    )

    # Create the payment record
    payment = Payment(
        booking_id=booking.id,
        reference=tx_ref,
        amount=amount,
        status="pending",
        provider="flutterwave",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    # Initialize payment with Flutterwave
    payment_link = initialize_payment(
        tx_ref=tx_ref,
        amount=amount,
        currency=currency,
        redirect_url="http://localhost:8000/payments/callback",
        customer_email=current_user.email,
        customer_name=current_user.full_name,
    )

    # Save the Flutterwave payment link
    payment.payment_link = payment_link

    db.commit()
    db.refresh(payment)

    return {
        "payment_id": payment.id,
        "booking_id": booking.id,
        "tx_ref": tx_ref,
        "amount": amount,
        "currency": currency,
        "payment_link": payment_link,
        "status": payment.status,
    }


@router.get(
    "/",
    response_model=list[PaymentResponse],
)
def get_payments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    payments = (
        db.query(Payment)
        .join(
            Booking,
            Payment.booking_id == Booking.id,
        )
        .filter(
            Booking.user_id == current_user.id,
        )
        .order_by(Payment.id.desc())
        .all()
    )

    return payments


@router.post("/verify")
def verify_booking_payment(
    payment_data: PaymentVerifyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    transaction = verify_transaction(
        payment_data.transaction_id
    )

    transaction_data = transaction.get(
        "data",
        {},
    )

    tx_ref = transaction_data.get("tx_ref")
    amount = transaction_data.get("amount")
    currency = transaction_data.get("currency")
    status = transaction_data.get("status")

    if not tx_ref:
        raise HTTPException(
            status_code=400,
            detail="Transaction reference missing from Flutterwave response",
        )

    payment = db.query(Payment).filter(
        Payment.reference == tx_ref
    ).first()

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment record not found",
        )

    booking = db.query(Booking).filter(
        Booking.id == payment.booking_id,
        Booking.user_id == current_user.id,
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found",
        )

    # Idempotency:
    # If the payment was already successfully processed,
    # don't change it back to another status.
    if payment.status == "paid":
        return {
            "message": "Payment already verified",
            "payment_id": payment.id,
            "booking_id": payment.booking_id,
            "reference": payment.reference,
            "amount": payment.amount,
            "currency": "NGN",
            "status": payment.status,
        }

    if amount != payment.amount:
        raise HTTPException(
            status_code=400,
            detail="Payment amount does not match booking amount",
        )

    if currency != "NGN":
        raise HTTPException(
            status_code=400,
            detail="Payment currency does not match expected currency",
        )

    if status != "successful":
        payment.status = "failed"

        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Payment was not successful",
        )

    payment.status = "paid"

    db.commit()
    db.refresh(payment)

    return {
        "message": "Payment verified successfully",
        "payment_id": payment.id,
        "booking_id": payment.booking_id,
        "reference": payment.reference,
        "amount": payment.amount,
        "currency": currency,
        "status": payment.status,
    }


@router.get("/callback")
def payment_callback(
    status: str,
    tx_ref: str,
    transaction_id: int | None = None,
):
    if status == "successful" and transaction_id:
        return {
            "message": (
                "Payment completed. "
                "Transaction is ready for verification."
            ),
            "tx_ref": tx_ref,
            "transaction_id": transaction_id,
            "status": status,
        }

    return {
        "message": "Payment was not completed.",
        "tx_ref": tx_ref,
        "transaction_id": transaction_id,
        "status": status,
    }