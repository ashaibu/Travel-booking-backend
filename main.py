import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import flights, buses, ships, auth, bookings, users, payments


load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development")

app = FastAPI(
    title="Travel Booking API",
    description="API for booking flights, buses, and ships.",
    version="1.0.0",
)

if APP_ENV == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
def root():
    return {"status": "ok", "message": "Travel Booking API is running"}


app.include_router(flights.router)
app.include_router(buses.router)
app.include_router(ships.router)
app.include_router(auth.router)
app.include_router(bookings.router)
app.include_router(users.router)
app.include_router(payments.router)