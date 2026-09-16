from fastapi import FastAPI
from app.routers import flights, buses

app = FastAPI()

app.include_router(flights.router)
app.include_router(buses.router)