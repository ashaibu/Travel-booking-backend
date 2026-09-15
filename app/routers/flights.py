from fastapi import APIRouter, HTTPException
from app.schemas.flight import FlightResponse, FlightCreate

router = APIRouter()


flights = [
    {
        "id": 1,
        "airline": "Air Peace",
        "from": "Lagos",
        "to": "Abuja",
        "departure": "10:00",
        "arrival": "11:10",
        "price": 150000,
        "available_seats": 24
    },
    {
        "id": 2,
        "airline": "Ibom Air",
        "from": "Lagos",
        "to": "Abuja",
        "departure": "14:00",
        "arrival": "15:10",
        "price": 140000,
        "available_seats": 18
    }
]


@router.get("/flights/{flight_id}", response_model=FlightResponse)
def get_flight(flight_id: int):

    for flight in flights:
        if flight["id"] == flight_id:
            return flight

    raise HTTPException(
        status_code=404,
        detail="Flight not found"
    )


@router.post("/flights", response_model=FlightResponse)
def create_flight(flight: FlightCreate):

    new_flight = {
        "id": len(flights) + 1,
        "airline": flight.airline,
        "from": flight.from_,
        "to": flight.to,
        "departure": flight.departure,
        "arrival": flight.arrival,
        "price": flight.price,
        "available_seats": flight.available_seats
    }

    flights.append(new_flight)

    return new_flight


@router.put("/flights/{flight_id}", response_model=FlightResponse)
def update_flight(flight_id: int, updated_flight: FlightCreate):

    for flight in flights:
        if flight["id"] == flight_id:
            flight["airline"] = updated_flight.airline
            flight["from"] = updated_flight.from_
            flight["to"] = updated_flight.to
            flight["departure"] = updated_flight.departure
            flight["arrival"] = updated_flight.arrival
            flight["price"] = updated_flight.price
            flight["available_seats"] = updated_flight.available_seat


        return flight

    raise HTTPException(
        status_code=404,
        detail="Flight not found"
    )

@router.delete("/flights/{fligth_id}")
def delete_flight(flight_id: int): 

    for flight in flights:
            if flight["id"] == flight_id: 
                flights.remove(flight) 
                return {"message": "Flight deleted successfully"}

    raise HTTPException(
        status_code=404,
        detail="flight not found"
    )

@router.get("/flights", response_model=list[FlightResponse])
def get_flights():

    return  flights 