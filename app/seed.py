from sqlalchemy import select
from app.database import engine, new_session, Base
from app.models import User, Role, Permission
from app.auth import hash_password


async def init_db_async():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables ensured")

    async with new_session() as session:
        stmt = select(Role)
        result = await session.execute(stmt)
        if result.scalars().first():
            print("Database already initialized, skipping seed")
            return

        # --- Создаём данные, только если их нет ---
        permissions_data = [
            ("user", "read"),
            ("user", "update"),
            ("user", "delete"),
            ("role", "read"),
            ("role", "create"),
            ("role", "update"),
            ("role", "delete"),
            ("permission", "read"),
            ("permission", "create"),
            ("permission", "update"),
            ("permission", "delete"),
            ("resource", "read"),
        ]
        perms = []
        for resource, action in permissions_data:
            p = Permission(
                resource=resource, action=action, name=f"{resource}:{action}"
            )
            session.add(p)
            perms.append(p)

        # Роли
        admin_role = Role(name="admin", description="Administrator")
        admin_role.permissions = perms
        session.add(admin_role)

        user_role = Role(name="user", description="Regular user")
        read_perm = await session.execute(
            select(Permission).where(
                Permission.resource == "resource", Permission.action == "read"
            )
        )
        read_perm = read_perm.scalars().first()
        if read_perm:
            user_role.permissions.append(read_perm)
        session.add(user_role)

        # Пользователи
        admin_user = User(
            email="admin@example.com",
            hashed_password=hash_password("admin123"),
            first_name="Admin",
            last_name="User",
            is_active=True,
            roles=[admin_role],
        )
        session.add(admin_user)

        normal_user = User(
            email="user@example.com",
            hashed_password=hash_password("user123"),
            first_name="Regular",
            last_name="User",
            is_active=True,
            roles=[user_role],
        )
        session.add(normal_user)

        print("Admin roles before commit:", [r.name for r in admin_user.roles])
        print("User roles before commit:", [r.name for r in normal_user.roles])

        await session.commit()
        print("Test data created")
