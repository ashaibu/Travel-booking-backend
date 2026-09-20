from fastapi import APIRouter, Depends, HTTPException 
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate 
from app.services.dependencies import get_current_admin


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    users = db.query(User).all()

    return users

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user 



@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    updated_user: UserUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if updated_user.full_name is not None:
        user.full_name = updated_user.full_name

    if updated_user.email is not None:
        user.email = updated_user.email

    if updated_user.role is not None:
        user.role = updated_user.role

    if updated_user.is_active is not None:
        user.is_active = updated_user.is_active

    db.commit()
    db.refresh(user)

    return user