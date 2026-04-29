from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.db.database import get_db
from app.models.models import AppUser, UserRole

router = APIRouter()

PASSWORD_MIN_LEN = 8


def _validate_password(password: str) -> str | None:
    if len(password) < PASSWORD_MIN_LEN:
        return f"Password must be at least {PASSWORD_MIN_LEN} characters"
    if not any(c.isalpha() for c in password):
        return "Password must contain at least one letter"
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one number"
    return None


def require_admin(user: AppUser = Depends(get_current_user)) -> AppUser:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


class UserCreate(BaseModel):
    username: str
    password: str
    display_name: str | None = None
    role: str = "staff"
    must_change_password: bool = True


class PasswordChange(BaseModel):
    password: str


class UserUpdate(BaseModel):
    display_name: str | None = None
    role: str | None = None
    is_active: bool | None = None


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    _admin: AppUser = Depends(require_admin),
):
    return [u.to_dict() for u in db.query(AppUser).order_by(AppUser.created_at).all()]


@router.post("")
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _admin: AppUser = Depends(require_admin),
):
    if db.query(AppUser).filter(AppUser.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if not payload.username.strip():
        raise HTTPException(status_code=422, detail="Username cannot be empty")
    valid_roles = [r.value for r in UserRole]
    if payload.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Valid: {valid_roles}")
    err = _validate_password(payload.password)
    if err:
        raise HTTPException(status_code=422, detail=err)
    user = AppUser(
        username=payload.username.strip().lower(),
        password_hash=hash_password(payload.password),
        display_name=payload.display_name or payload.username,
        role=payload.role,
        must_change_password=payload.must_change_password,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.to_dict()


@router.patch("/{user_id}/password")
def admin_set_password(
    user_id: str,
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Admin sets a user's password (no old-password check). Staff must use /auth/me/password."""
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    err = _validate_password(payload.password)
    if err:
        raise HTTPException(status_code=422, detail=err)
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = hash_password(payload.password)
    user.must_change_password = False
    user.failed_login_count = 0
    user.locked_until = None
    db.commit()
    return {"ok": True}


@router.patch("/{user_id}/unlock")
def unlock_user(
    user_id: str,
    db: Session = Depends(get_db),
    _admin: AppUser = Depends(require_admin),
):
    """Admin unlocks a locked account and resets failed login counter."""
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.locked_until = None
    user.failed_login_count = 0
    db.commit()
    return user.to_dict()


@router.patch("/{user_id}/force-reset")
def force_password_reset(
    user_id: str,
    db: Session = Depends(get_db),
    _admin: AppUser = Depends(require_admin),
):
    """Force user to change password on next login."""
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.must_change_password = True
    db.commit()
    return user.to_dict()


@router.patch("/{user_id}")
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: AppUser = Depends(require_admin),
):
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.role is not None:
        valid_roles = [r.value for r in UserRole]
        if payload.role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"Invalid role. Valid: {valid_roles}")
        # Prevent admin from demoting themselves
        if current_admin.id == user_id and payload.role != UserRole.ADMIN:
            raise HTTPException(status_code=400, detail="Cannot change your own role")
        user.role = payload.role
    if payload.is_active is not None:
        if current_admin.id == user_id and not payload.is_active:
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user.to_dict()


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_admin: AppUser = Depends(require_admin),
):
    if current_admin.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"ok": True}

