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
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    # AWS / S3 — optional; if AWS_S3_BUCKET is set, photos go to S3 instead of local disk
    AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_CLOUDFRONT_URL: str = os.getenv("AWS_CLOUDFRONT_URL", "")  # e.g. https://d1234.cloudfront.net


settings = Settings()
