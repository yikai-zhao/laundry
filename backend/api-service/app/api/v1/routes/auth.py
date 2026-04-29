from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.models.models import AppUser

router = APIRouter()

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def _validate_password_strength(password: str) -> str | None:
    """Return error message if password is too weak, else None."""
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if not any(c.isalpha() for c in password):
        return "Password must contain at least one letter"
    if not any(c.isdigit() for c in password):
        return "Password must contain at least one number"
    return None


class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(AppUser).filter(AppUser.username == payload.username).first()

    # Generic "invalid credentials" for unknown users (no username enumeration)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check account active
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled. Contact your administrator.")

    # Check lockout
    now = datetime.now(timezone.utc)
    if user.locked_until:
        locked_until = user.locked_until.replace(tzinfo=timezone.utc) if user.locked_until.tzinfo is None else user.locked_until
        if now < locked_until:
            remaining = int((locked_until - now).total_seconds() / 60) + 1
            raise HTTPException(
                status_code=429,
                detail=f"Account temporarily locked due to too many failed attempts. Try again in {remaining} minute(s)."
            )
        else:
            # Lockout expired — reset
            user.locked_until = None
            user.failed_login_count = 0

    if not verify_password(payload.password, user.password_hash):
        user.failed_login_count = (user.failed_login_count or 0) + 1
        remaining_attempts = max(0, MAX_FAILED_ATTEMPTS - user.failed_login_count)
        if user.failed_login_count >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
            db.commit()
            raise HTTPException(
                status_code=429,
                detail=f"Account locked for {LOCKOUT_MINUTES} minutes after too many failed attempts."
            )
        db.commit()
        if remaining_attempts <= 2:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid credentials. {remaining_attempts} attempt(s) remaining before lockout."
            )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Successful login
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token({"sub": user.id, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user.to_dict(),
    }


@router.get("/me")
def me(user: AppUser = Depends(get_current_user)):
    return user.to_dict()


@router.put("/me/password")
def change_own_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Self-service password change — requires current password verification."""
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    err = _validate_password_strength(payload.new_password)
    if err:
        raise HTTPException(status_code=422, detail=err)

    if verify_password(payload.new_password, current_user.password_hash):
        raise HTTPException(status_code=422, detail="New password must be different from the current password")

    user = db.query(AppUser).filter(AppUser.id == current_user.id).first()
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    db.commit()
    db.refresh(user)
    return {"ok": True, "user": user.to_dict()}

