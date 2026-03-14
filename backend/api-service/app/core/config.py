import os


class Settings:
    SECRET_KEY: str = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./laundry.db")
    STORAGE_ROOT: str = os.getenv("STORAGE_ROOT", "./storage")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))  # 10MB
    ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


settings = Settings()
