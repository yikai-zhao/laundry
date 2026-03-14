from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.database import get_db
from app.models.models import AppUser, Customer

router = APIRouter()


class CustomerCreate(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None


@router.get("")
def list_customers(q: str = "", db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    query = db.query(Customer)
    if q:
        query = query.filter(Customer.name.ilike(f"%{q}%") | Customer.phone.ilike(f"%{q}%"))
    customers = query.order_by(Customer.created_at.desc()).limit(100).all()
    return [c.to_dict() for c in customers]


@router.post("")
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    customer = Customer(name=payload.name, phone=payload.phone, email=payload.email)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer.to_dict()


@router.get("/{customer_id}")
def get_customer(customer_id: str, db: Session = Depends(get_db), _user: AppUser = Depends(get_current_user)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    result = customer.to_dict()
    result["orders"] = [o.to_dict() for o in customer.orders]
    return result
