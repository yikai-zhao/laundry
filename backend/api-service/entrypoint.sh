#!/bin/sh
set -e

echo "==> Creating database tables..."
python -c "
from app.db.database import engine
from app.models.models import Base
Base.metadata.create_all(bind=engine)
print('Tables created successfully.')
"

echo "==> Stamping Alembic to head..."
alembic stamp head

echo "==> Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
