"""
Authentication API endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserWithToken,
    Token,
    UserPasswordChange,
    UserUpdate,
    UserListResponse,
)
from app.api.deps import get_current_user, require_admin, get_current_active_user
from app.services.auth_service import (
    authenticate_user,
    create_user,
    create_access_token_for_user,
    get_user_by_id,
    change_password,
    update_user,
    delete_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()


@router.post("/register", response_model=UserWithToken, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    Regular users can register themselves. Default role is USER.
    """
    try:
        user = create_user(db, user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Generate token
    token, expires_in = create_access_token_for_user(user)
    
    return UserWithToken(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=bool(user.is_active),
        created_at=user.created_at.isoformat() if user.created_at else None,
        token=Token(
            access_token=token,
            expires_in=expires_in
        )
    )


@router.post("/login", response_model=Token)
def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    
    Returns JWT access token on success.
    """
    user = authenticate_user(db, login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token, expires_in = create_access_token_for_user(user)
    
    return Token(
        access_token=token,
        expires_in=expires_in
    )


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=bool(current_user.is_active),
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
    )


@router.put("/me", response_model=UserResponse)
def update_me(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.
    """
    try:
        updated_user = update_user(
            db,
            current_user,
            full_name=update_data.full_name,
            email=update_data.email
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        full_name=updated_user.full_name,
        role=updated_user.role,
        is_active=bool(updated_user.is_active),
        created_at=updated_user.created_at.isoformat() if updated_user.created_at else None,
    )


@router.post("/me/change-password")
def change_me_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change current user password.
    """
    success = change_password(
        db,
        current_user,
        password_data.current_password,
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    return {"message": "Password changed successfully"}


# Admin endpoints

@router.get("/users", response_model=UserListResponse, dependencies=[Depends(require_admin)])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all users (admin only).
    """
    total = db.query(User).count()
    users = db.query(User).offset(skip).limit(limit).all()
    
    return UserListResponse(
        total=total,
        users=[
            UserResponse(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                role=u.role,
                is_active=bool(u.is_active),
                created_at=u.created_at.isoformat() if u.created_at else None,
            )
            for u in users
        ]
    )


@router.get("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific user by ID (admin only).
    """
    user = get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=bool(user.is_active),
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
def delete_user_admin(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a user (admin only).
    """
    user = get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    delete_user(db, user)
    
    return {"message": "User deleted successfully"}
