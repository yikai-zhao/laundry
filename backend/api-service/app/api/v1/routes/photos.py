import os
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.image_quality import check_image_quality
from app.core.storage import delete_photo, save_photo
from app.db.database import get_db
from app.models.models import AppUser, GarmentPhoto, LaundryOrderItem

router = APIRouter()


@router.post("/order-items/{item_id}/photos")
async def upload_photo(
    item_id: str,
    file: UploadFile,
    photo_label: Optional[str] = Form(None),
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

    # Image quality check
    quality = check_image_quality(content)

    file_path, public_url = save_photo(content, ext)
    photo = GarmentPhoto(
        order_item_id=item_id,
        file_path=file_path,
        original_filename=file.filename,
        photo_label=photo_label,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    d = photo.to_dict()
    d["quality"] = quality
    return d


@router.get("/order-items/{item_id}/photos")
def list_photos(item_id: str, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    photos = db.query(GarmentPhoto).filter(GarmentPhoto.order_item_id == item_id).order_by(GarmentPhoto.created_at).all()
    return [photo.to_dict() for photo in photos]


@router.delete("/photos/{photo_id}")
def delete_photo_endpoint(photo_id: str, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    photo = db.query(GarmentPhoto).filter(GarmentPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    delete_photo(photo.file_path or "")
    db.delete(photo)
    db.commit()
    return {"ok": True}
