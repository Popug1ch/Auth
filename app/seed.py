import asyncio
from app.database import engine, new_session
from sqlalchemy import select
from app.models import Base, User, Role, Permission
from app.crud import create_user

async def init_db():
    # Создаём таблицы (если ещё не созданы)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with new_session() as session:
        # Проверяем, есть ли уже роли
        stmt = select(Role)
        result = await session.execute(stmt)
        if result.scalars().first():
            print("База уже инициализирована")
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
        await session.commit()
        admin_role = Role(name="admin", description="Administrator")
        session.add(admin_role)
        await session.commit()
        admin_role.permissions = perms
        await session.commit()


        user_role = Role(name="user", description="Regular user")
        session.add(user_role)
        await session.commit()
        read_perm = await session.execute(
            select(Permission).where(Permission.resource == "resource", Permission.action == "read")
        )
        read_perm = read_perm.scalars().first()
        if read_perm:
            user_role.permissions.append(read_perm)
            await session.commit()

        admin_user = await create_user(
            session,
            email="admin@example.com",
            password="admin123",
            first_name="Admin",
            last_name="User"
        )
        admin_user.roles.append(admin_role)
        await session.commit()

        normal_user = await create_user(
            session,
            email="user@example.com",
            password="user123",
            first_name="Regular",
            last_name="User"
        )
        normal_user.roles.append(user_role)
        await session.commit()

        print("Тестовые данные созданы")

if __name__ == "__main__":
    asyncio.run(init_db())