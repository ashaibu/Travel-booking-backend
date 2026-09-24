import os

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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


# Serve the frontend's static assets (css/, js/) directly.
# VERIFY: confirm these folder names match your project exactly.
app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/js", StaticFiles(directory="js"), name="js")


@app.get("/")
def root():
    # Serves the actual frontend page instead of a JSON status message.
    # NOTE: this replaces the old health-check response at "/" —
    # confirm with your backend teammate this is fine, since it changes
    # what GET / returns for anyone else relying on the old behavior.
    return FileResponse("index.html")


@app.get("/health")
def health():
    # Kept the old JSON health-check available at a separate path,
    # in case anything (monitoring, teammate's scripts) still expects it.
    return {"status": "ok", "message": "Travel Booking API is running"}


app.include_router(flights.router)
app.include_router(buses.router)
app.include_router(ships.router)
app.include_router(auth.router)
app.include_router(bookings.router)
app.include_router(users.router)
app.include_router(payments.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)