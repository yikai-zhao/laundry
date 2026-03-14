import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    STAFF = "staff"
    ADMIN = "admin"


class OrderStatus(str, enum.Enum):
    CREATED = "created"
    INSPECTION_PENDING = "inspection_pending"
    INSPECTION_COMPLETED = "inspection_completed"
    AWAITING_CONFIRMATION = "awaiting_customer_confirmation"
    CONFIRMED = "confirmed"


class InspectionStatus(str, enum.Enum):
    PENDING = "pending"
    DETECTING = "detecting"
    REVIEWING = "reviewing"
    COMPLETED = "completed"


class ConfirmationStatus(str, enum.Enum):
    PENDING = "pending"
    SIGNED = "signed"
    EXPIRED = "expired"


class AppUser(Base):
    __tablename__ = "app_users"
    id = Column(String, primary_key=True, default=_uuid)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default=UserRole.STAFF)
    display_name = Column(String)
    created_at = Column(DateTime, default=_now)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Customer(Base):
    __tablename__ = "customers"
    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String)
    created_at = Column(DateTime, default=_now)

    orders = relationship("LaundryOrder", back_populates="customer")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LaundryOrder(Base):
    __tablename__ = "laundry_orders"
    id = Column(String, primary_key=True, default=_uuid)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    status = Column(String, default=OrderStatus.CREATED)
    note = Column(Text)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("LaundryOrderItem", back_populates="order", cascade="all, delete-orphan")
    confirmations = relationship("CustomerConfirmation", back_populates="order")

    def to_dict(self, include_details: bool = False):
        d = {
            "id": self.id,
            "customer_id": self.customer_id,
            "status": self.status,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_details:
            d["customer"] = self.customer.to_dict() if self.customer else None
            d["items"] = [item.to_dict() for item in self.items]
            confs = sorted(self.confirmations, key=lambda c: c.created_at, reverse=True) if self.confirmations else []
            d["confirmation"] = confs[0].to_dict() if confs else None
        return d


class LaundryOrderItem(Base):
    __tablename__ = "laundry_order_items"
    id = Column(String, primary_key=True, default=_uuid)
    order_id = Column(String, ForeignKey("laundry_orders.id"), nullable=False)
    garment_type = Column(String, nullable=False)
    color = Column(String)
    brand = Column(String)
    note = Column(Text)
    created_at = Column(DateTime, default=_now)

    order = relationship("LaundryOrder", back_populates="items")
    photos = relationship("GarmentPhoto", back_populates="order_item", cascade="all, delete-orphan")
    inspection = relationship("InspectionRecord", back_populates="order_item", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "garment_type": self.garment_type,
            "color": self.color,
            "brand": self.brand,
            "note": self.note,
            "photos": [p.to_dict() for p in self.photos],
            "inspection": self.inspection.to_dict() if self.inspection else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class GarmentPhoto(Base):
    __tablename__ = "garment_photos"
    id = Column(String, primary_key=True, default=_uuid)
    order_item_id = Column(String, ForeignKey("laundry_order_items.id"), nullable=False)
    file_path = Column(String, nullable=False)
    original_filename = Column(String)
    created_at = Column(DateTime, default=_now)

    order_item = relationship("LaundryOrderItem", back_populates="photos")

    def to_dict(self):
        return {
            "id": self.id,
            "order_item_id": self.order_item_id,
            "file_path": self.file_path,
            "original_filename": self.original_filename,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class InspectionRecord(Base):
    __tablename__ = "inspection_records"
    id = Column(String, primary_key=True, default=_uuid)
    order_item_id = Column(String, ForeignKey("laundry_order_items.id"), nullable=False)
    status = Column(String, default=InspectionStatus.PENDING)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    order_item = relationship("LaundryOrderItem", back_populates="inspection")
    issues = relationship("InspectionIssue", back_populates="inspection", cascade="all, delete-orphan")
    ai_results = relationship("InspectionAIResult", back_populates="inspection", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "order_item_id": self.order_item_id,
            "status": self.status,
            "issues": [i.to_dict() for i in self.issues],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class InspectionIssue(Base):
    __tablename__ = "inspection_issues"
    id = Column(String, primary_key=True, default=_uuid)
    inspection_id = Column(String, ForeignKey("inspection_records.id"), nullable=False)
    issue_type = Column(String, nullable=False)
    severity_level = Column(Integer, default=1)
    position_desc = Column(String)
    bbox_x = Column(Float)
    bbox_y = Column(Float)
    bbox_w = Column(Float)
    bbox_h = Column(Float)
    confidence_score = Column(Float)
    source = Column(String, default="manual")
    created_at = Column(DateTime, default=_now)

    inspection = relationship("InspectionRecord", back_populates="issues")

    def to_dict(self):
        return {
            "id": self.id,
            "inspection_id": self.inspection_id,
            "issue_type": self.issue_type,
            "severity_level": self.severity_level,
            "position_desc": self.position_desc,
            "bbox_x": self.bbox_x,
            "bbox_y": self.bbox_y,
            "bbox_w": self.bbox_w,
            "bbox_h": self.bbox_h,
            "confidence_score": self.confidence_score,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class InspectionAIResult(Base):
    __tablename__ = "inspection_ai_results"
    id = Column(String, primary_key=True, default=_uuid)
    inspection_id = Column(String, ForeignKey("inspection_records.id"), nullable=False)
    raw_result = Column(Text)
    created_at = Column(DateTime, default=_now)

    inspection = relationship("InspectionRecord", back_populates="ai_results")


class CustomerConfirmation(Base):
    __tablename__ = "customer_confirmations"
    id = Column(String, primary_key=True, default=_uuid)
    order_id = Column(String, ForeignKey("laundry_orders.id"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, default=ConfirmationStatus.PENDING)
    customer_name = Column(String)
    created_at = Column(DateTime, default=_now)
    confirmed_at = Column(DateTime)

    order = relationship("LaundryOrder", back_populates="confirmations")
    signature = relationship("SignatureRecord", back_populates="confirmation", uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "token": self.token,
            "status": self.status,
            "customer_name": self.customer_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "signature": self.signature.to_dict() if self.signature else None,
        }


class SignatureRecord(Base):
    __tablename__ = "signature_records"
    id = Column(String, primary_key=True, default=_uuid)
    confirmation_id = Column(String, ForeignKey("customer_confirmations.id"), nullable=False)
    signature_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_now)

    confirmation = relationship("CustomerConfirmation", back_populates="signature")

    def to_dict(self):
        return {
            "id": self.id,
            "confirmation_id": self.confirmation_id,
            "signature_data": self.signature_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
