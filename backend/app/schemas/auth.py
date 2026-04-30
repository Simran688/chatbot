"""
Pydantic schemas for authentication.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


# Token schemas
class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: Optional[int] = None  # user_id
    exp: Optional[int] = None  # expiration timestamp


# User registration/login schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User registration request."""
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.USER


class UserCreateAdmin(UserBase):
    """Admin user creation (by admin only)."""
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class UserPasswordChange(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


# User response schemas
class UserResponse(UserBase):
    """User response (safe - no password)."""
    id: int
    role: UserRole
    is_active: bool
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserWithToken(UserResponse):
    """User response with token."""
    token: Token


class UserListResponse(BaseModel):
    """List of users (admin only)."""
    total: int
    users: list[UserResponse]


class UserUpdate(BaseModel):
    """User profile update."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
