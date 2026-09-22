import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException


BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(
    BASE_DIR / ".env",
    override=True,
)


FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")
FLW_SECRET_HASH = os.getenv("FLW_SECRET_HASH")

FLW_BASE_URL = "https://api.flutterwave.com/v3"


def initialize_payment(
    tx_ref: str,
    amount: int,
    currency: str,
    redirect_url: str,
    customer_email: str,
    customer_name: str,
):
    """Create a Flutterwave hosted payment and return its payment link."""

    if not FLW_SECRET_KEY:
        raise RuntimeError(
            "FLW_SECRET_KEY is not configured"
        )

    payload = {
        "tx_ref": tx_ref,
        "amount": amount,
        "currency": currency,
        "redirect_url": redirect_url,
        "customer": {
            "email": customer_email,
            "name": customer_name,
        },
    }

    headers = {
        "Authorization": f"Bearer {FLW_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(
            f"{FLW_BASE_URL}/payments",
            json=payload,
            headers=headers,
            timeout=30.0,
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to Flutterwave",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Flutterwave payment initialization failed",
        )

    data = response.json()

    if data.get("status") != "success":
        raise HTTPException(
            status_code=502,
            detail="Flutterwave rejected the payment request",
        )

    payment_link = data.get("data", {}).get("link")

    if not payment_link:
        raise HTTPException(
            status_code=502,
            detail="Flutterwave did not return a payment link",
        )

    return payment_link


def verify_transaction(transaction_id: int):
    """Verify a Flutterwave transaction by transaction ID."""

    if not FLW_SECRET_KEY:
        raise RuntimeError(
            "FLW_SECRET_KEY is not configured"
        )

    headers = {
        "Authorization": f"Bearer {FLW_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.get(
            f"{FLW_BASE_URL}/transactions/"
            f"{transaction_id}/verify",
            headers=headers,
            timeout=30.0,
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to Flutterwave",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Flutterwave transaction verification failed",
        )

    data = response.json()

    if data.get("status") != "success":
        raise HTTPException(
            status_code=400,
            detail="Flutterwave could not verify the transaction",
        )

    return data