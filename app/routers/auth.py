from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.database import SessionDep
from app.schemas import UserCreate, UserLogin, Token
from app.repository.user_repository import UserRepository
from app.auth import (
    verify_password,
    create_access_token,
    add_token_to_blacklist,
    decode_token,
)
from app.dependencies import oauth2_scheme
from app.models import Role
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, session: SessionDep):
    existing = await UserRepository.get_by_email(session, user_data.email)
    if existing:
        raise HTTPException(400, "Email already registered")
    user = await UserRepository.create(
        session,
        email=user_data.email,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        father_name=user_data.father_name,
    )
    stmt = select(Role).where(Role.name == "user")
    result = await session.execute(stmt)
    role = result.scalars().first()
    if role:
        user.roles.append(role)
        await session.commit()
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, session: SessionDep):
    user = await UserRepository.get_by_email(session, login_data.email)
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(401, "User inactive")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout", status_code=204)
async def logout(session: SessionDep, token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(400, "Token required")
    payload = decode_token(token)
    if payload:
        expires_at = datetime.utcfromtimestamp(payload.get("exp"))
        await add_token_to_blacklist(session, token, expires_at)
    return
