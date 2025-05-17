from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum
from app.db.models import UserRole

# User creation schema
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    
    @validator("password")
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

# User update schema
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    tokens_remaining: Optional[int] = None
    active: Optional[bool] = None
    role: Optional[UserRole] = None
    
    @validator("password")
    def password_min_length(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

# User output schema
class UserOut(BaseModel):
    id: str = Field(..., alias="_id")
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole
    tokens_remaining: int
    created_at: datetime
    active: bool
    
    class Config:
        allow_population_by_field_name = True

# Admin user manipulation schema
class AdminUserCreate(UserCreate):
    role: UserRole
    tokens_remaining: int = Field(default=100)

# Admin user update schema
class AdminUserUpdate(UserUpdate):
    pass
