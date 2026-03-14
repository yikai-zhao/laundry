from fastapi import APIRouter

from app.api.v1.routes import auth, confirmations, customers, inspections, issues, order_items, orders, photos

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(order_items.router, tags=["order-items"])
api_router.include_router(photos.router, tags=["photos"])
api_router.include_router(inspections.router, tags=["inspections"])
api_router.include_router(issues.router, prefix="/issues", tags=["issues"])
api_router.include_router(confirmations.router, prefix="/confirmations", tags=["confirmations"])
