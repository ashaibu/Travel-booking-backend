import secrets

from fastapi import APIRouter, Depends, HTTPException
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
    initialize_payment,
    verify_transaction,
)


router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


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
