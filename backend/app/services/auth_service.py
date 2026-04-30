"""
Authentication service for user management.
"""

from datetime import timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
)
from app.core.config import settings
from app.schemas.auth import UserCreate, UserLogin


def authenticate_user(
    db: Session,
    email: str,
    password: str
) -> Optional[User]:
    """
    Authenticate user with email and password.
    
    Args:
        db: Database session
        email: User email
        password: Plain text password
        
    Returns:
        User if authenticated, None otherwise
    """
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return None
    
    if not user.is_active:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        user_data: User creation data
        
    Returns:
        Created user
    """
    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise ValueError("Email already registered")
    
    # Create user
    db_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=1,
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def create_access_token_for_user(user: User) -> Tuple[str, int]:
    """
    Create JWT access token for user.
    
    Args:
        user: User object
        
    Returns:
        Tuple of (token, expires_in_seconds)
    """
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return token, expires_in


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Get user by ID.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        User or None
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get user by email.
    
    Args:
        db: Database session
        email: User email
        
    Returns:
        User or None
    """
    return db.query(User).filter(User.email == email).first()


def change_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str
) -> bool:
    """
    Change user password.
    
    Args:
        db: Database session
        user: User object
        current_password: Current plain text password
        new_password: New plain text password
        
    Returns:
        True if password changed successfully
    """
    # Verify current password
    if not verify_password(current_password, user.hashed_password):
        return False
    
    # Update password
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return True


def update_user(
    db: Session,
    user: User,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    is_active: Optional[bool] = None,
    role: Optional[UserRole] = None,
) -> User:
    """
    Update user profile.
    
    Args:
        db: Database session
        user: User object
        full_name: New full name (optional)
        email: New email (optional)
        is_active: New active status (optional)
        role: New role (optional)
        
    Returns:
        Updated user
    """
    if full_name is not None:
        user.full_name = full_name
    
    if email is not None:
        # Check if email is already taken
        existing = db.query(User).filter(
            User.email == email,
            User.id != user.id
        ).first()
        if existing:
            raise ValueError("Email already registered")
        user.email = email
    
    if is_active is not None:
        user.is_active = 1 if is_active else 0
    
    if role is not None:
        user.role = role
    
    db.commit()
    db.refresh(user)
    
    return user


def delete_user(db: Session, user: User) -> bool:
    """
    Delete a user.
    
    Args:
        db: Database session
        user: User to delete
        
    Returns:
        True if deleted
    """
    db.delete(user)
    db.commit()
    return True
