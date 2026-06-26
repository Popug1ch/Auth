from sqlalchemy import select
from app.models import User

async def create_user(session, email, hashed_password, first_name, last_name, father_name=None):
    user = User(
        email=email,
        hashed_password=hashed_password,
        first_name=first_name,
        last_name=last_name,
        father_name=father_name,
        is_active=True
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_user_by_email(session, email):
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalars().first()

async def get_user_by_id(session, user_id):
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    return result.scalars().first()