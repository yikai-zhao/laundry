from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.database import get_db
from app.models.models import AppUser, LaundryOrder, LaundryOrderItem, OrderStatus

router = APIRouter()


class ItemCreate(BaseModel):
    garment_type: str
    color: str | None = None
    brand: str | None = None
    note: str | None = None


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
