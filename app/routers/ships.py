from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.ship import ShipResponse, ShipCreate
from app.database.database import get_db
from app.models.ship import Ship
from app.services.dependencies import get_current_user 


router = APIRouter()


@router.post("/ships", response_model=ShipResponse)
def create_ship(
    ship: ShipCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    new_ship = Ship(
        operator=ship.operator,
        from_=ship.from_,
        to=ship.to,
        departure=ship.departure,
        arrival=ship.arrival,
        price=ship.price,
        available_seats=ship.available_seats
    )

    db.add(new_ship)
    db.commit()
    db.refresh(new_ship)

    return new_ship


@router.put("/ships/{ship_id}", response_model=ShipResponse)
def update_ship(
    ship_id: int,
    updated_ship: ShipCreate,
    db: Session = Depends(get_db)
):
    ship = db.query(Ship).filter(Ship.id == ship_id).first()

    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    ship.operator = updated_ship.operator
    ship.from_ = updated_ship.from_
    ship.to = updated_ship.to
    ship.departure = updated_ship.departure
    ship.arrival = updated_ship.arrival
    ship.price = updated_ship.price
    ship.available_seats = updated_ship.available_seats

    db.commit()
    db.refresh(ship)

    return ship


@router.delete("/ships/{ship_id}")
def delete_ship(ship_id: int, db: Session = Depends(get_db)):
    ship = db.query(Ship).filter(Ship.id == ship_id).first()

    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")

    db.delete(ship)
    db.commit()

    return {"message": "Ship deleted successfully"}