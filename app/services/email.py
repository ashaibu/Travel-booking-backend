from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
import os
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


async def send_email(
    recipient: EmailStr,
    subject: str,
    body: str
):
    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=body,
        subtype="html"
    )

    fm = FastMail(conf)

    await fm.send_message(message)  


async def send_booking_confirmation(
    recipient: EmailStr,
    ticket_number: str,
    transport_type: str,
    transport_id: int
):
    subject = "Travel Booking Confirmation"

    body = f"""
    <html>
        <body>
            <h2>Booking Confirmed</h2>

            <p>Your travel booking has been confirmed.</p>

            <p><strong>Ticket Number:</strong> {ticket_number}</p>
            <p><strong>Transport Type:</strong> {transport_type}</p>
            <p><strong>Transport ID:</strong> {transport_id}</p>

            <p>Thank you for booking with us.</p>
        </body>
    </html>
    """

    await send_email(
        recipient=recipient,
        subject=subject,
        body=body
    )