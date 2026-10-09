"""
ASAA Travel — Python/Flask port of the original Go/Gin backend.

Same routes, same in-memory data shapes, same behavior:
  - unified login (admin credentials checked first, then customer accounts)
  - destination pricing lookup/upsert (admin can create AND edit price tags)
  - ticket applications with quote + payment confirmation flow
  - per-customer "My Tickets" history
  - secrets read from environment variables (with local-dev fallbacks)
"""

import os
import random
import smtplib
import threading
from datetime import datetime
from email.mime.text import MIMEText

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


@app.get("/health")
def health_check():
    return jsonify({"status": "ok"})


def env_or_default(key: str, fallback: str) -> str:
    """Read an environment variable, falling back to a default for local dev."""
    return os.environ.get(key) or fallback


# ---------------------------------------------------------------------------
# Config / secrets — same env var names as the Go version.
# ---------------------------------------------------------------------------
ADMIN_USERNAME = env_or_default("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = env_or_default("ADMIN_PASSWORD", "adminpassword123")

SMTP_EMAIL = env_or_default("SMTP_EMAIL", "your-email@gmail.com")
SMTP_APP_PASSWORD = env_or_default("SMTP_APP_PASSWORD", "your-app-password")
SMTP_HOST = env_or_default("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(env_or_default("SMTP_PORT", "587"))

# Flutterwave PUBLIC key — safe to expose client-side by design.
FLUTTERWAVE_PUBLIC_KEY = env_or_default(
    "FLUTTERWAVE_PUBLIC_KEY", "FLWPUBK_TEST-YOUR_PUBLIC_KEY_HERE-X"
)

# ---------------------------------------------------------------------------
# In-memory data — same shape as the Go version's maps/slices, guarded by
# locks the same way sync.Mutex guarded them.
# ---------------------------------------------------------------------------
users_lock = threading.Lock()
users = {
    "traveler@example.com": {
        "name": "John Doe",
        "email": "traveler@example.com",
        "password": "user123",
        "phone": "+2348000000000",
    }
}

applications_lock = threading.Lock()
applications = []  # list of application dicts
app_seq_id = 1001

pricing_lock = threading.Lock()
pricing_rules = {
    "Lagos - Air": 85000.00,
    "Abuja - Air": 95000.00,
    "Lagos - Road": 12000.00,
    "Abuja - Road": 15000.00,
    "Calabar - Sea": 25000.00,
}


def capitalize(value: str) -> str:
    """Mirrors the Go version's capitalize(): normalizes a transport type."""
    if not value:
        return value
    v = value.lower()
    if v == "air":
        return "Air"
    if v == "road":
        return "Road"
    if v == "sea":
        return "Sea"
    return value


# ---------------------------------------------------------------------------
# HTML routes
# ---------------------------------------------------------------------------
@app.get("/")
def index():
    return render_template("index.html")


@app.get("/login")
def login_page():
    """Single login page — handles BOTH customer and admin sign-in."""
    return render_template("login.html")


@app.get("/register")
def register_page():
    return render_template("register.html")


@app.get("/book")
def book_page():
    transport_type = request.args.get("type") or "road"
    return render_template(
        "book.html",
        type=transport_type,
        flutterwave_public_key=FLUTTERWAVE_PUBLIC_KEY,
    )


@app.get("/admin")
def admin_page():
    return render_template("admin.html")


@app.get("/my-tickets")
def my_tickets_page():
    return render_template("my_tickets.html")


# ---------------------------------------------------------------------------
# Auth APIs
# ---------------------------------------------------------------------------
@app.post("/api/auth/register")
def handle_user_register():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    if not email:
        return jsonify({"error": "Invalid registration input"}), 400

    with users_lock:
        if email in users:
            return jsonify({"error": "Account with this email already exists"}), 409
        users[email] = {
            "name": data.get("name", ""),
            "email": email,
            "password": data.get("password", ""),
            "phone": data.get("phone", ""),
        }

    return jsonify({"status": "success", "message": "Registration successful. Please log in."})


@app.post("/api/auth/login")
def handle_login():
    """
    Unified login: tries the admin credentials first (identifier = admin
    username), then falls back to looking the identifier up as a customer
    email.
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")

    # 1. Admin check
    if email == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return jsonify({"status": "success", "role": "admin", "message": "Admin authenticated"})

    # 2. Customer check
    with users_lock:
        user = users.get(email)

    if not user or user["password"] != password:
        return jsonify({"error": "Invalid email/username or password"}), 401

    return jsonify(
        {
            "status": "success",
            "role": "customer",
            "user": {"name": user["name"], "email": user["email"], "phone": user["phone"]},
        }
    )


# ---------------------------------------------------------------------------
# Application & price APIs
# ---------------------------------------------------------------------------
@app.post("/api/submit-application")
def handle_submit_application():
    global app_seq_id
    data = request.get_json(silent=True) or {}

    with applications_lock:
        req_id = app_seq_id
        app_seq_id += 1

        transport_type = data.get("transport_type", "")
        destination = data.get("destination", "")
        pricing_key = f"{destination} - {capitalize(transport_type)}"

        with pricing_lock:
            price = pricing_rules.get(pricing_key)

        if price is not None:
            quoted_price = price
            status = "Quoted"
        else:
            quoted_price = 0.0
            status = "Pending Admin Price"

        record = {
            "id": req_id,
            "user_email": data.get("user_email", ""),
            "user_name": data.get("user_name", ""),
            "phone": data.get("phone", ""),
            "destination": destination,
            "transport_type": transport_type,
            "date": data.get("date", ""),
            "time": data.get("time", ""),
            "quoted_price": quoted_price,
            "status": status,
            "seat_number": "",
            "applied_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        applications.append(record)

    return jsonify(
        {
            "status": "success",
            "application_id": req_id,
            "quoted_price": quoted_price,
            "review_status": status,
            "message": "Application submitted successfully.",
        }
    )


@app.get("/api/get-price")
def handle_get_price():
    dest = request.args.get("destination", "")
    transport_type = request.args.get("type", "")
    key = f"{dest} - {capitalize(transport_type)}"

    with pricing_lock:
        price = pricing_rules.get(key)

    if price is not None:
        return jsonify({"status": "available", "price": price})
    return jsonify({"status": "pending_admin", "price": 0.0})


@app.post("/api/confirm-booking")
def handle_booking_confirmation():
    data = request.get_json(silent=True) or {}
    application_id = data.get("application_id")
    amount = data.get("amount", 0.0)

    seat_number = f"Seat-{random.randint(1, 40)}{random.choice('ABCD')}"

    updated_app = None
    with applications_lock:
        for a in applications:
            if a["id"] == application_id:
                a["status"] = "Paid & Ticket Issued"
                a["seat_number"] = seat_number
                updated_app = dict(a)  # snapshot for the email thread
                break

    if updated_app:
        threading.Thread(
            target=send_ticket_email,
            args=(
                updated_app["user_email"],
                updated_app["user_name"],
                updated_app["transport_type"],
                updated_app["destination"],
                updated_app["date"],
                updated_app["time"],
                seat_number,
                amount,
            ),
            daemon=True,
        ).start()

    return jsonify(
        {
            "status": "success",
            "seat_number": seat_number,
            "message": "Booking confirmed, application status updated, and ticket dispatched.",
        }
    )


@app.get("/api/my-applications")
def get_my_applications():
    """A single customer's own applications (their ticket history), scoped by email."""
    email = request.args.get("email", "")
    if not email:
        return jsonify({"error": "Missing email"}), 400

    with applications_lock:
        my_apps = [a for a in applications if a["user_email"] == email]

    return jsonify(my_apps)


# ---------------------------------------------------------------------------
# Admin dashboard data APIs
# ---------------------------------------------------------------------------
@app.get("/api/admin/applications")
def get_admin_applications():
    with applications_lock:
        return jsonify(applications)


@app.post("/api/admin/quote-price")
def quote_application_price():
    data = request.get_json(silent=True) or {}
    app_id = data.get("id")
    price = data.get("price")

    with applications_lock:
        for a in applications:
            if a["id"] == app_id:
                a["quoted_price"] = price
                a["status"] = "Quoted by Admin"
                return jsonify({"status": "success", "message": "Price quoted successfully"})

    return jsonify({"error": "Application record not found"}), 404


@app.get("/api/admin/pricing")
def get_pricing_rules():
    with pricing_lock:
        return jsonify(pricing_rules)


@app.post("/api/admin/pricing")
def update_pricing_rule():
    """
    Upsert by "Destination - Mode" key — posting the SAME destination+mode
    again simply overwrites the existing price. This is how the admin
    dashboard both creates NEW price tags and EDITS existing ones.
    """
    data = request.get_json(silent=True) or {}
    destination = data.get("destination", "")
    transport_type = data.get("transport_type", "")
    price = data.get("price")

    key = f"{destination} - {transport_type}"
    with pricing_lock:
        pricing_rules[key] = price

    return jsonify({"status": "success", "message": "Pricing set successfully"})


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
def send_ticket_email(to_email, name, transport_type, dest, date, time_str, seat_number, amount):
    subject = "Your ASAA Travel Application & Ticket Confirmation"
    body = f"""
        <h2>Ticket Application Confirmed - ASAA Travel</h2>
        <p>Hello <strong>{name}</strong>,</p>
        <p>Your travel ticket application has been successfully paid and processed!</p>
        <hr>
        <h3>Application Details:</h3>
        <ul>
            <li><strong>Traveler Name:</strong> {name}</li>
            <li><strong>Transport Mode:</strong> {transport_type}</li>
            <li><strong>Destination:</strong> {dest}</li>
            <li><strong>Travel Date:</strong> {date}</li>
            <li><strong>Departure Time:</strong> {time_str}</li>
            <li><strong>Total Fare Paid:</strong> ₦{amount:.2f}</li>
            <li><strong>Assigned Seat Number:</strong> {seat_number}</li>
        </ul>
        <p>Please present this confirmation email at departure.</p>
        <p>Safe Travels,<br>ASAA Travel Team</p>
    """

    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
            server.sendmail(SMTP_EMAIL, [to_email], msg.as_string())
    except Exception as e:  # noqa: BLE001 — mirrors the Go version's swallow-and-log
        print(f"failed to send ticket email to {to_email}: {e}")


if __name__ == "__main__":
    # Render (and most hosts) assign the port dynamically via $PORT — the
    # app MUST listen on that, not a hardcoded port, or the deploy will
    # fail health checks.
    port = int(env_or_default("PORT", "8080"))
    print(f"ASAA Travel Server running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port)
