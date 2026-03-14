import os
import shutil
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.db.database import get_db
from app.models.models import AppUser, GarmentPhoto, LaundryOrderItem

router = APIRouter()

PHOTO_DIR = "storage/photos"


@router.post("/order-items/{item_id}/photos")
async def upload_photo(
    item_id: str,
    file: UploadFile,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
):
    item = db.query(LaundryOrderItem).filter(LaundryOrderItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    ext = os.path.splitext(file.filename or "img.jpg")[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed. Use: {', '.join(settings.ALLOWED_EXTENSIONS)}")
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max {settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB")
    os.makedirs(PHOTO_DIR, exist_ok=True)
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(PHOTO_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)
    photo = GarmentPhoto(
        order_item_id=item_id,
        file_path=f"/storage/photos/{filename}",
        original_filename=file.filename,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo.to_dict()


@router.get("/order-items/{item_id}/photos")
def list_photos(item_id: str, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    photos = db.query(GarmentPhoto).filter(GarmentPhoto.order_item_id == item_id).order_by(GarmentPhoto.created_at).all()
    return [p.to_dict() for p in photos]


@router.delete("/photos/{photo_id}")
def delete_photo(photo_id: str, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    photo = db.query(GarmentPhoto).filter(GarmentPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    try:
        if photo.file_path:
            path = photo.file_path.lstrip("/")
            if os.path.exists(path):
                os.remove(path)
    except OSError:
        pass
    db.delete(photo)
    db.commit()
    return {"ok": True}
