from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.bus import BusResponse, BusCreate
from app.database.database import get_db
from app.models.bus import Bus
from app.services.dependencies import get_current_user

router = APIRouter()


@router.post("/buses", response_model=BusResponse)
def create_bus(
    bus: BusCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    new_bus = Bus(
        operator=bus.operator,
        from_=bus.from_,
        to=bus.to,
        departure=bus.departure,
        arrival=bus.arrival,
        price=bus.price,
        available_seats=bus.available_seats
    )

    db.add(new_bus)
    db.commit()
    db.refresh(new_bus)

    return new_bus




@router.get("/buses", response_model=list[BusResponse])
def get_buses(db: Session = Depends(get_db)):
    buses = db.query(Bus).all()
    return buses


@router.get("/buses/{bus_id}", response_model=BusResponse)
def get_bus(
    bus_id: int,
    db: Session = Depends(get_db)
):
    bus = db.query(Bus).filter(Bus.id == bus_id).first()

    if not bus:
        raise HTTPException(
            status_code=404,
            detail="Bus not found"
        )

    return bus


@router.put("/buses/{bus_id}", response_model=BusResponse)
def update_bus(
    bus_id: int,
    updated_bus: BusCreate,
    db: Session = Depends(get_db)
):
    bus = db.query(Bus).filter(Bus.id == bus_id).first()

    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    bus.operator = updated_bus.operator
    bus.from_ = updated_bus.from_
    bus.to = updated_bus.to
    bus.departure = updated_bus.departure
    bus.arrival = updated_bus.arrival
    bus.price = updated_bus.price
    bus.available_seats = updated_bus.available_seats

    db.commit()
    db.refresh(bus)

    return bus


@router.delete("/buses/{bus_id}")
def delete_bus(bus_id: int, db: Session = Depends(get_db)):
    bus = db.query(Bus).filter(Bus.id == bus_id).first()

    if not bus:
        raise HTTPException(status_code=404, detail="Bus not found")

    db.delete(bus)
    db.commit()

    return {"message": "Bus deleted successfully"}



