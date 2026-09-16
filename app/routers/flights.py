from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.flight import FlightResponse, FlightCreate
from app.database.database import get_db
from app.models.flight import Flight

router = APIRouter()



@router.get("/flights/{flight_id}", response_model=FlightResponse)
def get_flight(flight_id: int, db: Session = Depends(get_db)):
    flight = db.query(Flight).filter(Flight.id == flight_id).first()

    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    return flight


@router.post("/flights", response_model=FlightResponse)
def create_flight(flight: FlightCreate, db: Session = Depends(get_db)):
    new_flight = Flight(
        airline=flight.airline,
        from_=flight.from_,
        to=flight.to,
        departure=flight.departure,
        arrival=flight.arrival,
        price=flight.price,
        available_seats=flight.available_seats
    )

    db.add(new_flight)
    db.commit()
    db.refresh(new_flight)

    return new_flight




@router.put("/flights/{flight_id}", response_model=FlightResponse)
def update_flight(
    flight_id: int,
    updated_flight: FlightCreate,
    db: Session = Depends(get_db)
):
    flight = db.query(Flight).filter(Flight.id == flight_id).first()

    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    flight.airline = updated_flight.airline
    flight.from_ = updated_flight.from_
    flight.to = updated_flight.to
    flight.departure = updated_flight.departure
    flight.arrival = updated_flight.arrival
    flight.price = updated_flight.price
    flight.available_seats = updated_flight.available_seats

    db.commit()
    db.refresh(flight)

    return flight



@router.delete("/flights/{flight_id}")
def delete_flight(flight_id: int, db: Session = Depends(get_db)):
    flight = db.query(Flight).filter(Flight.id == flight_id).first()

    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    db.delete(flight)
    db.commit()

    return {"message": "Flight deleted successfully"}



@router.get("/flights", response_model=list[FlightResponse])
def get_flights(db: Session = Depends(get_db)):
    flights = db.query(Flight).all()

    return flights