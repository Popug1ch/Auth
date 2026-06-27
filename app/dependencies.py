from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from app.database import SessionDep
from app.auth import decode_token, is_token_blacklisted
from app.repository.user_repository import UserRepository
from app.models import User, Role, Permission

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(session: SessionDep, token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if await is_token_blacklisted(session, token):
        raise HTTPException(status_code=401, detail="Token revoked")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await UserRepository.get_by_id(session, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user


def require_admin(
    session: SessionDep, current_user: User = Depends(get_current_active_user)
):
    for role in current_user.roles:
        if role.name == "admin":
            return current_user
    raise HTTPException(status_code=403, detail="Admin rights required")


def require_permission(resource: str, action: str):
    async def permission_checker(
        session: SessionDep, current_user: User = Depends(get_current_active_user)
    ):
        for role in current_user.roles:
            if role.name == "admin":
                return current_user
        stmt = (
            select(Permission)
            .join(Role.permissions)
            .join(User.roles)
            .where(
                User.id == current_user.id,
                Permission.resource == resource,
                Permission.action == action,
            )
        )
        result = await session.execute(stmt)
        if result.scalars().first() is None:
            raise HTTPException(status_code=403, detail="Permission denied")
        return current_user

    return permission_checker
