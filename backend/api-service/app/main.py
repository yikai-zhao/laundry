import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.security import hash_password
from app.db.database import SessionLocal, engine
from app.models.models import AppUser, Base, UserRole


def create_app() -> FastAPI:
    application = FastAPI(title="Laundry AI Inspection System", version="0.1.0")

    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    if "*" in origins:
        origins = ["*"]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix="/api/v1")

    @application.on_event("startup")
    def on_startup():
        Base.metadata.create_all(bind=engine)
        os.makedirs("storage/photos", exist_ok=True)
        os.makedirs("storage/signatures", exist_ok=True)
        db = SessionLocal()
        try:
            # Seed default accounts if none exist
            if not db.query(AppUser).first():
                db.add(AppUser(
                    username="admin",
                    password_hash=hash_password("admin123"),
                    role=UserRole.ADMIN,
                    display_name="Admin",
                    must_change_password=True,
                ))
                db.add(AppUser(
                    username="staff",
                    password_hash=hash_password("staff123"),
                    role=UserRole.STAFF,
                    display_name="Staff",
                    must_change_password=True,
                ))
                db.commit()

            # One-time emergency reset via env var:
            # RESET_CREDENTIALS=admin:Admin@2026,staff:Staff@2026
            reset_env = os.environ.get("RESET_CREDENTIALS", "").strip()
            if reset_env:
                for entry in reset_env.split(","):
                    parts = entry.strip().split(":", 1)
                    if len(parts) == 2:
                        uname, pw = parts
                        user = db.query(AppUser).filter(AppUser.username == uname).first()
                        if user:
                            user.password_hash = hash_password(pw)
                            user.must_change_password = False
                            user.failed_login_count = 0
                            user.locked_until = None
                db.commit()
                print(f"[RESET] Credentials reset via RESET_CREDENTIALS env var")
        finally:
            db.close()

    @application.get("/health")
    def health():
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            return {"status": "ok", "database": "connected"}
        except Exception as e:
            return {"status": "degraded", "database": str(e)}

    storage_dir = Path("storage")
    storage_dir.mkdir(parents=True, exist_ok=True)
    application.mount("/storage", StaticFiles(directory="storage"), name="storage")

    return application


app = create_app()
