from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    password_confirm: str
    first_name: str
    last_name: str
    father_name: Optional[str] = None

    @field_validator('password_confirm')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    father_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)

class UserOut(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    father_name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class PermissionCreate(BaseModel):
    resource: str
    action: str
    name: Optional[str] = None
    description: Optional[str] = None

class PermissionOut(PermissionCreate):
    id: int
    class Config:
        from_attributes = True

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permission_ids: List[int] = []

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None

class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    permissions: List[PermissionOut] = []
    class Config:
        from_attributes = True

class UserWithRoles(UserOut):
    roles: List[RoleOut] = []

class AssignRole(BaseModel):
    role_id: int