from fastapi import APIRouter, Depends, HTTPException
from app.database import SessionDep
from app.schemas import UserOut, UserUpdate
from app.dependencies import get_current_active_user
from app.models import User
from app.repository.user_repository import UserRepository
from app.auth import hash_password

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.put("/me", response_model=UserOut)
async def update_me(
    update_data: UserUpdate,
    session: SessionDep,
    current_user: User = Depends(get_current_active_user)
):
    if update_data.email:
        existing = await UserRepository.get_by_email(session, update_data.email)
        if existing and existing.id != current_user.id:
            raise HTTPException(400, "Email already taken")
    update_dict = update_data.dict(exclude_unset=True)
    if "password" in update_dict and update_dict["password"] is not None:
        update_dict["hashed_password"] = hash_password(update_dict.pop("password"))
    for key, value in update_dict.items():
        if hasattr(current_user, key) and value is not None:
            setattr(current_user, key, value)
    await session.commit()
    await session.refresh(current_user)
    return current_user

@router.delete("/me", status_code=204)
async def delete_me(
    session: SessionDep,
    current_user: User = Depends(get_current_active_user)
):
    await UserRepository.deactivate(session, current_user)
    return