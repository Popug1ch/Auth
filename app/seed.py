import asyncio
from sqlalchemy import select
from app.database import engine, new_session, Base
from app.models import User, Role, Permission


async def init_db_async():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created")

    async with new_session() as session:
        stmt = select(Role)
        result = await session.execute(stmt)
        if result.scalars().first():
            print("Database already initialized, skipping seed")
            return

        permissions_data = [
            ("user", "read"), ("user", "update"), ("user", "delete"),
            ("role", "read"), ("role", "create"), ("role", "update"), ("role", "delete"),
            ("permission", "read"), ("permission", "create"), ("permission", "update"), ("permission", "delete"),
            ("resource", "read"),
        ]
        perms = []
        for resource, action in permissions_data:
            p = Permission(resource=resource, action=action, name=f"{resource}:{action}")
            session.add(p)
            perms.append(p)

        admin_role = Role(name="admin", description="Administrator")
        admin_role.permissions = perms
        session.add(admin_role)

        user_role = Role(name="user", description="Regular user")
        read_perm = await session.execute(
            select(Permission).where(Permission.resource == "resource", Permission.action == "read")
        )
        read_perm = read_perm.scalars().first()
        if read_perm:
            user_role.permissions.append(read_perm)
        session.add(user_role)

        admin_user = User(
            email="admin@example.com",
            hashed_password="admin123",
            first_name="Admin",
            last_name="User",
            is_active=True
        )
        admin_user.roles.append(admin_role)
        session.add(admin_user)

        normal_user = User(
            email="user@example.com",
            hashed_password="user123",
            first_name="Regular",
            last_name="User",
            is_active=True
        )
        normal_user.roles.append(user_role)
        session.add(normal_user)
        await session.commit()
        print("Test data created")