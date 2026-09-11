from fastapi import APIRouter

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


@router.get("/flights")
def get_flights():
    return {
        "flights": flights
    }