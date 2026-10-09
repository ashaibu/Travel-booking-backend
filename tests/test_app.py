"""
PERSON 4 — UI/UX + TESTING + ADMIN

Covers: registration, login, trip search, booking creation, "My Tickets"
listing, and the admin trip/bookings views.

Payment VERIFICATION (payments/verify) is intentionally not tested here —
it calls the real Flutterwave API over the network with the secret key,
which this suite has no sandbox credentials or network access for.
/payments/initiate (no external call) IS tested.

Run with:  pytest
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import hash_password
from app.database import Base, get_db
from app.main import ADMIN_EMAIL, ADMIN_PASSWORD, app
from app.models import User

# ---- Isolated in-memory test database --------------------------------
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def fresh_db():
    """
    Wipe and recreate all tables before every test, and seed the admin
    account directly against the TEST database. (app.main's seed_admin()
    only runs via FastAPI's startup event against the real engine, which
    this isolated test DB doesn't share — so we do it ourselves here.)
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    db.add(User(name="Admin", email=ADMIN_EMAIL, password_hash=hash_password(ADMIN_PASSWORD), is_admin=True))
    db.commit()
    db.close()

    yield


@pytest.fixture
def client():
    return TestClient(app)


def register_and_login(client, email="jane@mailbox.ng", password="pass1234"):
    client.post(
        "/auth/register",
        json={"name": "Jane Doe", "email": email, "phone": "+2348000000001", "password": password},
    )
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def make_admin_token(client):
    resp = client.post("/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


# ---- Auth ----------------------------------------------------------------
def test_register_then_login(client):
    resp = client.post(
        "/auth/register",
        json={"name": "Jane Doe", "email": "jane@mailbox.ng", "phone": "+234...", "password": "pass1234"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_admin"] is False

    resp = client.post("/auth/login", json={"email": "jane@mailbox.ng", "password": "pass1234"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password_fails(client):
    client.post(
        "/auth/register",
        json={"name": "Jane Doe", "email": "jane@mailbox.ng", "phone": "+234...", "password": "pass1234"},
    )
    resp = client.post("/auth/login", json={"email": "jane@mailbox.ng", "password": "wrong"})
    assert resp.status_code == 401


def test_duplicate_registration_fails(client):
    payload = {"name": "Jane Doe", "email": "jane@mailbox.ng", "phone": "+234...", "password": "pass1234"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 409


# ---- Admin seeding + trip management ----------------------------------
def test_admin_can_create_and_list_trip(client):
    token = make_admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/admin/trips",
        headers=headers,
        json={
            "mode": "flight",
            "operator_name": "Green Africa",
            "origin": "Lagos",
            "destination": "Abuja",
            "departure_time": "2026-12-01T07:00:00",
            "price": 85000,
            "total_seats": 40,
        },
    )
    assert resp.status_code == 201, resp.text
    trip = resp.json()
    assert trip["available_seats"] == 40

    resp = client.get("/admin/trips", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_non_admin_cannot_access_admin_routes(client):
    token = register_and_login(client)
    resp = client.get("/admin/trips", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


# ---- Trip search (flights/buses/ships) --------------------------------
def test_search_flights_filters_by_mode(client):
    admin_token = make_admin_token(client)
    headers = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        "/admin/trips",
        headers=headers,
        json={
            "mode": "bus", "operator_name": "GUO Transport", "origin": "Lagos",
            "destination": "Benin", "departure_time": "2026-12-01T07:00:00",
            "price": 12000, "total_seats": 18,
        },
    )
    client.post(
        "/admin/trips",
        headers=headers,
        json={
            "mode": "flight", "operator_name": "Green Africa", "origin": "Lagos",
            "destination": "Abuja", "departure_time": "2026-12-01T09:00:00",
            "price": 85000, "total_seats": 40,
        },
    )

    resp = client.get("/flights")
    assert resp.status_code == 200
    flights = resp.json()
    assert len(flights) == 1
    assert flights[0]["operator_name"] == "Green Africa"

    resp = client.get("/buses")
    assert len(resp.json()) == 1


# ---- Booking flow --------------------------------------------------------
def test_create_booking_reserves_a_seat(client):
    admin_token = make_admin_token(client)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    trip = client.post(
        "/admin/trips",
        headers=admin_headers,
        json={
            "mode": "flight", "operator_name": "Green Africa", "origin": "Lagos",
            "destination": "Abuja", "departure_time": "2026-12-01T09:00:00",
            "price": 85000, "total_seats": 2,
        },
    ).json()

    user_token = register_and_login(client)
    user_headers = {"Authorization": f"Bearer {user_token}"}

    resp = client.post(
        "/bookings",
        headers=user_headers,
        json={
            "trip_id": trip["id"],
            "seat_number": "12A",
            "passenger_name": "Jane Doe",
            "passenger_phone": "+2348000000001",
        },
    )
    assert resp.status_code == 201, resp.text
    booking = resp.json()
    assert booking["status"] == "pending_payment"
    assert booking["booking_ref"].startswith("BK-")

    # seat count dropped
    flight = client.get(f"/flights/{trip['id']}").json()
    assert flight["available_seats"] == 1


def test_my_tickets_only_shows_own_bookings(client):
    admin_token = make_admin_token(client)
    trip = client.post(
        "/admin/trips",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "mode": "ship", "operator_name": "Lagos Ferry Co", "origin": "Lagos",
            "destination": "Calabar", "departure_time": "2026-12-01T09:00:00",
            "price": 25000, "total_seats": 10,
        },
    ).json()

    token_a = register_and_login(client, email="a@mailbox.ng")
    token_b = register_and_login(client, email="b@mailbox.ng")

    client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"trip_id": trip["id"], "seat_number": "1A", "passenger_name": "A", "passenger_phone": "+234"},
    )

    resp_a = client.get("/bookings", headers={"Authorization": f"Bearer {token_a}"})
    resp_b = client.get("/bookings", headers={"Authorization": f"Bearer {token_b}"})

    assert len(resp_a.json()) == 1
    assert len(resp_b.json()) == 0


def test_payment_initiate_returns_public_key(client):
    """Covers /payments/initiate — no external network call, safe to test."""
    admin_token = make_admin_token(client)
    trip = client.post(
        "/admin/trips",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "mode": "flight", "operator_name": "Green Africa", "origin": "Lagos",
            "destination": "Abuja", "departure_time": "2026-12-01T09:00:00",
            "price": 85000, "total_seats": 5,
        },
    ).json()

    user_token = register_and_login(client)
    headers = {"Authorization": f"Bearer {user_token}"}
    booking = client.post(
        "/bookings",
        headers=headers,
        json={"trip_id": trip["id"], "seat_number": "3B", "passenger_name": "Jane", "passenger_phone": "+234"},
    ).json()

    resp = client.post("/payments/initiate", headers=headers, json={"booking_id": booking["id"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["tx_ref"].startswith("TGP-")
    assert data["amount"] == 85000
    assert data["currency"] == "NGN"


def test_cancel_booking_releases_seat(client):
    admin_token = make_admin_token(client)
    trip = client.post(
        "/admin/trips",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "mode": "bus", "operator_name": "GUO", "origin": "Lagos",
            "destination": "Ibadan", "departure_time": "2026-12-01T09:00:00",
            "price": 5000, "total_seats": 1,
        },
    ).json()

    user_token = register_and_login(client)
    headers = {"Authorization": f"Bearer {user_token}"}
    booking = client.post(
        "/bookings",
        headers=headers,
        json={"trip_id": trip["id"], "seat_number": "1A", "passenger_name": "Jane", "passenger_phone": "+234"},
    ).json()

    assert client.get(f"/buses/{trip['id']}").json()["available_seats"] == 0

    resp = client.post(f"/bookings/{booking['id']}/cancel", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"
    assert client.get(f"/buses/{trip['id']}").json()["available_seats"] == 1
