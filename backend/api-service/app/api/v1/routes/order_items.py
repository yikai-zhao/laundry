from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.storage import delete_photo
from app.db.database import get_db
from app.models.models import AppUser, GarmentPhoto, LaundryOrder, LaundryOrderItem, OrderStatus

router = APIRouter()


class ItemCreate(BaseModel):
    garment_type: str
    color: str | None = None
    brand: str | None = None
    note: str | None = None
    unit_price: float = 0.0
    service_type: str = "dry_clean"
    fabric_type: str | None = None
    has_lining: bool = False


@router.post("/orders/{order_id}/items")
def create_item(order_id: str, payload: ItemCreate, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    order = db.query(LaundryOrder).filter(LaundryOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    item = LaundryOrderItem(
        order_id=order_id,
        garment_type=payload.garment_type,
        color=payload.color,
        brand=payload.brand,
        note=payload.note,
        unit_price=payload.unit_price,
        service_type=payload.service_type,
        fabric_type=payload.fabric_type,
        has_lining=payload.has_lining,
    )
    db.add(item)
    if order.status == OrderStatus.CREATED:
        order.status = OrderStatus.INSPECTION_PENDING
    db.commit()
    db.refresh(item)
    return item.to_dict()


@router.get("/order-items/{item_id}")
def get_item(item_id: str, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    item = db.query(LaundryOrderItem).filter(LaundryOrderItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item.to_dict()


@router.delete("/order-items/{item_id}")
def delete_item(item_id: str, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    item = db.query(LaundryOrderItem).filter(LaundryOrderItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


class ItemUpdate(BaseModel):
    unit_price: float | None = None
    note: str | None = None
    color: str | None = None
    brand: str | None = None
    service_type: str | None = None
    fabric_type: str | None = None
    has_lining: bool | None = None


@router.patch("/order-items/{item_id}")
def update_item(item_id: str, payload: ItemUpdate, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    item = db.query(LaundryOrderItem).filter(LaundryOrderItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if payload.unit_price is not None:
        item.unit_price = payload.unit_price
    if payload.note is not None:
        item.note = payload.note
    if payload.color is not None:
        item.color = payload.color
    if payload.brand is not None:
        item.brand = payload.brand
    if payload.service_type is not None:
        item.service_type = payload.service_type
    if payload.fabric_type is not None:
        item.fabric_type = payload.fabric_type
    if payload.has_lining is not None:
        item.has_lining = payload.has_lining
    db.commit()
    db.refresh(item)
    return item.to_dict()


@router.delete("/order-items/{item_id}/photos/{photo_id}")
def delete_photo_endpoint(
    item_id: str,
    photo_id: str,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
):
    photo = db.query(GarmentPhoto).filter(
        GarmentPhoto.id == photo_id,
        GarmentPhoto.order_item_id == item_id,
    ).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    delete_photo(photo.file_path)
    if photo.annotated_file_path:
        delete_photo(photo.annotated_file_path)
    db.delete(photo)
    db.commit()
    return {"ok": True}
