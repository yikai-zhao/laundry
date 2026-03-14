from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.security import hash_password
from app.db.database import get_db
from app.models.models import AppUser, UserRole

router = APIRouter()


def require_admin(user: AppUser = Depends(get_current_user)) -> AppUser:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


class UserCreate(BaseModel):
    username: str
    password: str
    display_name: str | None = None
    role: str = "staff"


class PasswordChange(BaseModel):
    password: str


class UserUpdate(BaseModel):
    display_name: str | None = None
    role: str | None = None


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
    valid_roles = [r.value for r in UserRole]
    if payload.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Valid: {valid_roles}")
    user = AppUser(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name or payload.username,
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.to_dict()


@router.patch("/{user_id}/password")
def change_password(
    user_id: str,
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Admin can change any password; staff can only change their own
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if not payload.password or len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    user = db.query(AppUser).filter(AppUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = hash_password(payload.password)
    db.commit()
    return {"ok": True}


@router.patch("/{user_id}")
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _admin: AppUser = Depends(require_admin),
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
        user.role = payload.role
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
