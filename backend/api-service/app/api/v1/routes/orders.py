import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.api.v1.deps import get_current_user
from app.db.database import get_db
from app.models.models import (
    AppUser,
    ConfirmationStatus,
    Customer,
    CustomerConfirmation,
    LaundryOrder,
    LaundryOrderItem,
    OrderStatus,
    UserRole,
)

router = APIRouter()


class OrderCreate(BaseModel):
    customer_id: str
    note: str | None = None


@router.get("")
def list_orders(
    status: str | None = None,
    q: str = "",
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
):
    if limit > 200:
        limit = 200
    query = db.query(LaundryOrder).options(joinedload(LaundryOrder.customer))
    if status:
        query = query.filter(LaundryOrder.status == status)
    if q:
        query = query.join(Customer).filter(
            Customer.name.ilike(f"%{q}%") | Customer.phone.ilike(f"%{q}%")
        )
    else:
        query = query.join(Customer, isouter=True)
    total = query.count()
    orders = query.order_by(LaundryOrder.created_at.desc()).offset(skip).limit(limit).all()
    return [o.to_dict(include_details=True) for o in orders]


@router.post("")
def create_order(payload: OrderCreate, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    order = LaundryOrder(customer_id=payload.customer_id, note=payload.note)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order.to_dict(include_details=True)


@router.get("/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    order = (
        db.query(LaundryOrder)
        .options(
            joinedload(LaundryOrder.customer),
            joinedload(LaundryOrder.items),
            joinedload(LaundryOrder.confirmations),
        )
        .filter(LaundryOrder.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order.to_dict(include_details=True)


@router.post("/{order_id}/confirmation")
def generate_confirmation(order_id: str, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    order = db.query(LaundryOrder).filter(LaundryOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    existing = (
        db.query(CustomerConfirmation)
        .filter(CustomerConfirmation.order_id == order_id, CustomerConfirmation.status == ConfirmationStatus.PENDING)
        .first()
    )
    if existing:
        return existing.to_dict()
    token = secrets.token_urlsafe(32)
    confirmation = CustomerConfirmation(order_id=order_id, token=token)
    order.status = OrderStatus.AWAITING_CONFIRMATION
    db.add(confirmation)
    db.commit()
    db.refresh(confirmation)
    return confirmation.to_dict()


class StatusUpdate(BaseModel):
    status: str


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: str,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
):
    order = db.query(LaundryOrder).filter(LaundryOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    valid_statuses = [s.value for s in OrderStatus]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Valid: {valid_statuses}")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order.to_dict(include_details=True)


@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: str,
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
):
    order = db.query(LaundryOrder).filter(LaundryOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status == OrderStatus.PICKED_UP:
        raise HTTPException(status_code=400, detail="Cannot cancel an order that has already been picked up")
    order.status = OrderStatus.CANCELLED
    db.commit()
    return {"ok": True, "status": "cancelled"}


@router.delete("/{order_id}")
def delete_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required to delete orders")
    order = db.query(LaundryOrder).filter(LaundryOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    db.delete(order)
    db.commit()
    return {"ok": True}
