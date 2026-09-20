from fastapi import FastAPI
from app.routers import flights, buses, ships, auth, bookings, users  

app = FastAPI()

app.include_router(flights.router)
app.include_router(buses.router)
app.include_router(ships.router)
app.include_router(auth.router)
app.include_router(bookings.router) 
app.include_router(users.router) 