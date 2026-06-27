from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.auth import hash_password


class UserRepository:
    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def create(
        session: AsyncSession,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        father_name: str = None,
    ) -> User:
        hashed = hash_password(password)
        user = User(
            email=email,
            hashed_password=hashed,
            first_name=first_name,
            last_name=last_name,
            father_name=father_name,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def update(session: AsyncSession, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        if kwargs.get("password"):
            user.hashed_password = hash_password(kwargs["password"])
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def deactivate(session: AsyncSession, user: User) -> User:
        user.is_active = False
        await session.commit()
        await session.refresh(user)
        return user
