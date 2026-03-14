from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.models import (
    ConfirmationStatus,
    CustomerConfirmation,
    LaundryOrder,
    OrderStatus,
    SignatureRecord,
)

router = APIRouter()


class ConfirmationSubmit(BaseModel):
    customer_name: str
    signature_data: str


@router.get("/{token}")
def get_confirmation(token: str, db: Session = Depends(get_db)):
    conf = (
        db.query(CustomerConfirmation)
        .options(
            joinedload(CustomerConfirmation.order)
            .joinedload(LaundryOrder.customer),
            joinedload(CustomerConfirmation.order)
            .joinedload(LaundryOrder.items),
            joinedload(CustomerConfirmation.signature),
        )
        .filter(CustomerConfirmation.token == token)
        .first()
    )
    if not conf:
        raise HTTPException(status_code=404, detail="Confirmation not found")
    result = conf.to_dict()
    result["order"] = conf.order.to_dict(include_details=True)
    return result


@router.post("/{token}/submit")
def submit_confirmation(token: str, payload: ConfirmationSubmit, db: Session = Depends(get_db)):
    conf = db.query(CustomerConfirmation).filter(CustomerConfirmation.token == token).first()
    if not conf:
        raise HTTPException(status_code=404, detail="Confirmation not found")
    if conf.status == ConfirmationStatus.SIGNED:
        raise HTTPException(status_code=400, detail="Already signed")
    conf.status = ConfirmationStatus.SIGNED
    conf.customer_name = payload.customer_name
    conf.confirmed_at = datetime.now(timezone.utc)
    sig = SignatureRecord(confirmation_id=conf.id, signature_data=payload.signature_data)
    db.add(sig)
    order = db.query(LaundryOrder).filter(LaundryOrder.id == conf.order_id).first()
    if order:
        order.status = OrderStatus.CONFIRMED
    db.commit()
    db.refresh(conf)
    return conf.to_dict()
