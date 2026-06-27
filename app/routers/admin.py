from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from typing import List
from app.database import SessionDep
from app.dependencies import require_admin
from app.models import User, Role, Permission
from app.schemas import (
    UserWithRoles,
    RoleOut,
    RoleCreate,
    RoleUpdate,
    PermissionOut,
    PermissionCreate,
    AssignRole,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[UserWithRoles])
async def list_users(session: SessionDep, _=Depends(require_admin)):
    stmt = select(User)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/roles", response_model=List[RoleOut])
async def list_roles(session: SessionDep, _=Depends(require_admin)):
    stmt = select(Role)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("/roles", response_model=RoleOut, status_code=201)
async def create_role(
    role_data: RoleCreate, session: SessionDep, _=Depends(require_admin)
):
    existing = await session.execute(select(Role).where(Role.name == role_data.name))
    if existing.scalars().first():
        raise HTTPException(400, "Role already exists")
    role = Role(name=role_data.name, description=role_data.description)
    if role_data.permission_ids:
        perms = await session.execute(
            select(Permission).where(Permission.id.in_(role_data.permission_ids))
        )
        role.permissions = perms.scalars().all()
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role


@router.put("/roles/{role_id}", response_model=RoleOut)
async def update_role(
    role_id: int, role_data: RoleUpdate, session: SessionDep, _=Depends(require_admin)
):
    role = await session.get(Role, role_id)
    if not role:
        raise HTTPException(404, "Role not found")
    if role_data.name:
        existing = await session.execute(
            select(Role).where(Role.name == role_data.name, Role.id != role_id)
        )
        if existing.scalars().first():
            raise HTTPException(400, "Role name already taken")
        role.name = role_data.name
    if role_data.description is not None:
        role.description = role_data.description
    if role_data.permission_ids is not None:
        perms = await session.execute(
            select(Permission).where(Permission.id.in_(role_data.permission_ids))
        )
        role.permissions = perms.scalars().all()
    await session.commit()
    await session.refresh(role)
    return role


@router.delete("/roles/{role_id}", status_code=204)
async def delete_role(role_id: int, session: SessionDep, _=Depends(require_admin)):
    role = await session.get(Role, role_id)
    if not role:
        raise HTTPException(404, "Role not found")
    if role.name in ("admin", "user"):
        raise HTTPException(403, "Cannot delete system role")
    await session.delete(role)
    await session.commit()
    return


@router.get("/permissions", response_model=List[PermissionOut])
async def list_permissions(session: SessionDep, _=Depends(require_admin)):
    stmt = select(Permission)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("/permissions", response_model=PermissionOut, status_code=201)
async def create_permission(
    perm_data: PermissionCreate, session: SessionDep, _=Depends(require_admin)
):
    existing = await session.execute(
        select(Permission).where(
            Permission.resource == perm_data.resource,
            Permission.action == perm_data.action,
        )
    )
    if existing.scalars().first():
        raise HTTPException(400, "Permission already exists")
    perm = Permission(**perm_data.dict())
    session.add(perm)
    await session.commit()
    await session.refresh(perm)
    return perm


@router.put("/permissions/{perm_id}", response_model=PermissionOut)
async def update_permission(
    perm_id: int,
    perm_data: PermissionCreate,
    session: SessionDep,
    _=Depends(require_admin),
):
    perm = await session.get(Permission, perm_id)
    if not perm:
        raise HTTPException(404, "Permission not found")
    existing = await session.execute(
        select(Permission).where(
            Permission.resource == perm_data.resource,
            Permission.action == perm_data.action,
            Permission.id != perm_id,
        )
    )
    if existing.scalars().first():
        raise HTTPException(400, "Permission already exists")
    perm.resource = perm_data.resource
    perm.action = perm_data.action
    perm.name = perm_data.name
    perm.description = perm_data.description
    await session.commit()
    await session.refresh(perm)
    return perm


@router.delete("/permissions/{perm_id}", status_code=204)
async def delete_permission(
    perm_id: int, session: SessionDep, _=Depends(require_admin)
):
    perm = await session.get(Permission, perm_id)
    if not perm:
        raise HTTPException(404, "Permission not found")
    await session.delete(perm)
    await session.commit()
    return


@router.post("/users/{user_id}/roles", status_code=204)
async def assign_role(
    user_id: int, assignment: AssignRole, session: SessionDep, _=Depends(require_admin)
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    role = await session.get(Role, assignment.role_id)
    if not role:
        raise HTTPException(404, "Role not found")
    if role not in user.roles:
        user.roles.append(role)
        await session.commit()
    return


@router.delete("/users/{user_id}/roles/{role_id}", status_code=204)
async def remove_role(
    user_id: int, role_id: int, session: SessionDep, _=Depends(require_admin)
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    role = await session.get(Role, role_id)
    if not role:
        raise HTTPException(404, "Role not found")
    if role in user.roles:
        user.roles.remove(role)
        await session.commit()
    return
