from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models import BlacklistedToken

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


async def add_token_to_blacklist(
    session: AsyncSession, token: str, expires_at: datetime
):
    db_token = BlacklistedToken(token=token, expires_at=expires_at)
    session.add(db_token)
    await session.commit()


async def is_token_blacklisted(session: AsyncSession, token: str) -> bool:
    stmt = select(BlacklistedToken).where(BlacklistedToken.token == token)
    result = await session.execute(stmt)
    return result.scalars().first() is not None
