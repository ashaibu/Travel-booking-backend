"""
PERSON 1 — BACKEND DEVELOPER

App entrypoint: creates tables, mounts every router, serves Person 2's
static frontend, and seeds one admin account on startup so there's
always someone who can log into /static/admin.html.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.auth import hash_password
from app.database import Base, SessionLocal, engine
from app.models import User
from app.routers import admin, auth, bookings, buses, flights, payments, ships, users

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@travelgroup.ng")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "adminpassword123")

Base.metadata.create_all(bind=engine)


def seed_admin():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.email == ADMIN_EMAIL).first():
            db.add(
                User(
                    name="Admin",
                    email=ADMIN_EMAIL,
                    password_hash=hash_password(ADMIN_PASSWORD),
                    is_admin=True,
                )
            )
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_admin()
    print(f"Admin login -> email: {ADMIN_EMAIL} | password: {ADMIN_PASSWORD}")
    yield


app = FastAPI(title="Travel Group Project API", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(flights.router)
app.include_router(buses.router)
app.include_router(ships.router)
app.include_router(bookings.router)
app.include_router(payments.router)
app.include_router(admin.router)


# ---- Static frontend (Person 2's pages) -----------------------------
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
