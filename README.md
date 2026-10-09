# TravelGroup — Multimodal Travel Booking Platform

FastAPI backend + static HTML/Tailwind/vanilla JS frontend, one repo, same
pattern as ASAA Travel but with a real SQLite database instead of
in-memory state, JWT auth instead of localStorage-only "sessions", and
**server-side Flutterwave payment verification** instead of trusting the
browser callback.

## Running it

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000`. A `travel.db` SQLite file is created
automatically, and an admin account is seeded on first startup (see
Environment Variables below for the login).

## Running the tests

```bash
pytest
```

10 tests, all passing — covers register/login, admin trip CRUD, trip
search per mode, booking creation + seat reservation, per-user "My
Tickets" scoping, payment initiation, and booking cancellation + seat
release. (Payment *verification* isn't tested — it calls the real
Flutterwave API with the secret key, which needs live sandbox
credentials and network access this test suite doesn't have.)

## Who owns what

```
travel-group-project/
├── app/
│   ├── main.py                  Person 1 — app entrypoint, routers, static mount, admin seed
│   ├── database.py              Person 1 — SQLAlchemy engine/session
│   ├── auth.py                  Person 1 — password hashing + JWT
│   ├── schemas.py                Person 1 — request/response shapes
│   ├── models/                  split by owner:
│   │   ├── user.py               Person 1 — User
│   │   ├── trip.py               Person 1 — Trip (flights/buses/ships share this table via `mode`)
│   │   ├── booking.py            Person 3 — Booking
│   │   └── payment.py            Person 3 — Payment
│   ├── services/
│   │   └── trips.py             Person 1 — shared search/CRUD logic used by all 3 mode routers
│   ├── routers/
│   │   ├── auth.py               Person 1 — register/login
│   │   ├── users.py              Person 1 — profile (GET/PUT /users/me)
│   │   ├── flights.py            Person 1 — GET /flights (mode="flight")
│   │   ├── buses.py              Person 1 — GET /buses   (mode="bus")
│   │   ├── ships.py              Person 1 — GET /ships   (mode="ship")
│   │   ├── bookings.py           Person 3 — seat reservation, booking ref, cancellation
│   │   ├── payments.py           Person 3 — Flutterwave initiate + SERVER-SIDE verify
│   │   └── admin.py              Person 4 — trip CRUD, bookings/payments/users oversight
│   └── static/                  Person 2 (you):
│       ├── index.html            Home — mode tabs + search
│       ├── search.html           Results list
│       ├── trip-details.html     Single trip + Book button
│       ├── login.html / register.html
│       ├── checkout.html         Passenger details + Flutterwave launch
│       ├── booking-confirmation.html
│       ├── my-tickets.html       Booking history
│       ├── profile.html
│       ├── admin.html            Person 4 — dashboard UI (trip management + bookings table)
│       ├── css/style.css         Person 2 / 4 — dark theme
│       └── js/
│           ├── api.js            Person 2 — every backend call lives here
│           └── app.js            Person 2 — per-page logic, dispatched by <body data-page="...">
├── tests/
│   └── test_app.py              Person 4 — pytest suite (isolated in-memory test DB)
├── requirements.txt
└── README.md
```

## Environment variables

| Key | Purpose | Default (local dev) |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./travel.db` |
| `JWT_SECRET` | Signs auth tokens — **set a real one in production** | `dev-secret-change-me` |
| `JWT_EXPIRE_MINUTES` | Token lifetime | `1440` (24h) |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Seeded admin login | `admin@travelgroup.ng` / `adminpassword123` |
| `FLUTTERWAVE_PUBLIC_KEY` | Sent to the browser for checkout | test placeholder |
| `FLUTTERWAVE_SECRET_KEY` | Used server-side to verify payments — **never expose this** | test placeholder |

## How the pieces connect

```
Browser (Person 2's static pages)
     │  fetch() via js/api.js, JWT in Authorization header
     ▼
FastAPI routers (Person 1: auth/users/flights/buses/ships,
                 Person 3: bookings/payments,
                 Person 4: admin)
     │  SQLAlchemy session
     ▼
SQLite (travel.db) — Users, Trips, Bookings, Payments
```

Booking + payment flow (checkout.html → app.js → api.js):
```
POST /bookings            → seat reserved, status="pending_payment"
POST /payments/initiate   → returns Flutterwave public key + tx_ref
FlutterwaveCheckout(...)  → browser opens payment modal
callback                  → POST /payments/verify
                              → backend calls Flutterwave's verify
                                endpoint SERVER-SIDE with the secret key,
                                checks amount/currency/status itself
                              → only THEN does status flip to "confirmed"
```

## Notes for whoever picks up Person 3 or Person 4's work next

- **Refunds** (`bookings.py::cancel_booking`) are stubbed — cancelling a
  *paid* booking releases the seat but doesn't call Flutterwave's refund
  API yet. Needs live secret-key credentials to build against.
- **Admin bookings/payments tables** are read-only in `admin.html` right
  now — no edit/refund actions wired up from the UI yet.
- Two real bugs came up building this that are worth knowing about if
  you touch auth: (1) `passlib`'s bcrypt backend breaks on
  `bcrypt>=4.1` — keep the `bcrypt==4.0.1` pin in `requirements.txt`
  unless you upgrade passlib too; (2) pydantic's `EmailStr` rejects
  RFC 2606 reserved domains (`example.com`, anything ending `.test`)
  — don't use those in seed data, fixtures, or demo accounts.
