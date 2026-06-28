from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.auth import decode_token, is_token_blacklisted
from app.models import User, Role

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if await is_token_blacklisted(db, token):
        raise HTTPException(status_code=401, detail="Token revoked")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    stmt = (
        select(User)
        .where(User.id == int(user_id))
        .options(selectinload(User.roles).selectinload(Role.permissions))
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    print(f"[DEBUG] User {user.email} roles: {[r.name for r in user.roles]}")

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user


def require_admin(current_user: User = Depends(get_current_active_user)):
    print(
        f"[DEBUG] require_admin called for user {current_user.email}, roles: {[r.name for r in current_user.roles]}"
    )
    for role in current_user.roles:
        if role.name == "admin":
            return current_user
    raise HTTPException(status_code=403, detail="Admin rights required")


def require_permission(resource: str, action: str):
    async def permission_checker(current_user: User = Depends(get_current_active_user)):
        for role in current_user.roles:
            if role.name == "admin":
                return current_user
            for perm in role.permissions:
                if perm.resource == resource and perm.action == action:
                    return current_user
        raise HTTPException(status_code=403, detail="Permission denied")

    return permission_checker
