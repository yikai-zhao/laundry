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
    OrderStatus,
)

router = APIRouter()


class OrderCreate(BaseModel):
    customer_id: str
    note: str | None = None


@router.get("")
def list_orders(
    status: str | None = None,
    q: str = "",
    db: Session = Depends(get_db),
    _user: AppUser = Depends(get_current_user),
):
    query = db.query(LaundryOrder).options(joinedload(LaundryOrder.customer))
    if status:
        query = query.filter(LaundryOrder.status == status)
    if q:
        query = query.join(Customer).filter(Customer.name.ilike(f"%{q}%"))
    orders = query.order_by(LaundryOrder.created_at.desc()).limit(200).all()
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
