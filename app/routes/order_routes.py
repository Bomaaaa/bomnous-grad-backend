import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from app.db import get_db
from app.utils.security import get_current_user
from app.models import User, Order, Product, OrderItem, Shop
from app.schemas.product import ProductResponse
import app.crud as crud


router = APIRouter(prefix="/orders", tags=["Orders"])
api_router = APIRouter(prefix="/api/orders", tags=["Orders"])
seller_api_router = APIRouter(prefix="/api/seller", tags=["Seller"])


def _serialize_order(db: Session, order: Order) -> dict:
    items_out = []
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        product_data = None
        if product:
            shop_name = db.query(Shop.name).filter(Shop.id == product.shop_id).scalar()
            pdata = ProductResponse.model_validate(product).model_dump()
            pdata["shop_name"] = shop_name
            product_data = pdata
        items_out.append(
            {
                "id": item.id,
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": product.price if product else 0,
                "product": product_data,
            }
        )
    return {
        "id": order.id,
        "status": order.status,
        "total": order.total_price,
        "total_price": order.total_price,
        "created_at": None,
        "items": items_out,
    }


def _list_my_orders(db: Session, current_user: User):
    orders = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.user_id == current_user.id)
        .order_by(Order.id.desc())
        .all()
    )
    return [_serialize_order(db, o) for o in orders]


@router.get("/")
def list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _list_my_orders(db, current_user)


@api_router.get("/")
def api_list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _list_my_orders(db, current_user)


@api_router.get("/seller")
def get_seller_orders_v2(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_seller_orders(db, current_user)


@api_router.get("/{order_id}")
def api_get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _serialize_order(db, order)


@router.post("/")
def create_order(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ("buyer", "seller"):
        raise HTTPException(
            status_code=403,
            detail="Sign in as a buyer or seller to place orders",
        )

    order = crud.create_order(db, current_user.id)
    return _serialize_order(db, order)


@api_router.post("/")
def api_create_order(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("buyer", "seller"):
        raise HTTPException(status_code=403, detail="Sign in as a buyer or seller to place orders")
    order = crud.create_order(db, current_user.id)
    return _serialize_order(db, order)


def _cancel_order(db: Session, order_id: int, current_user: User) -> dict:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not allowed to cancel this order")
    status = (order.status or "pending").lower()
    if status == "cancelled":
        return _serialize_order(db, order)
    if status not in ("pending", "processing", "confirmed"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order with status '{order.status}'",
        )
    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return _serialize_order(db, order)


@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _cancel_order(db, order_id, current_user)


@api_router.post("/{order_id}/cancel")
def api_cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _cancel_order(db, order_id, current_user)


@router.post("/{order_id}/add")
def add_product(
    order_id: int, 
    product_id: int, 
    quantity: int,
    db: Session = Depends(get_db),  
    current_user: User = Depends(get_current_user)
):
    # 1️⃣ Fetch the order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 2️⃣ Ensure the current user owns the order
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not allowed to modify this order")

    # 3️⃣ Fetch the product and validate
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")

    if product.stock < quantity:
        raise HTTPException(status_code=400, detail=f"Not enough stock for {product.name}")

    # 4️⃣ Check if the product is already in the order
    existing_item = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order_id, OrderItem.product_id == product_id)
        .first()
    )

    # 5️⃣ Deduct stock and update/add order item
    product.stock -= quantity

    if existing_item:
        existing_item.quantity += quantity
    else:
        new_item = OrderItem(order_id=order_id, product_id=product_id, quantity=quantity)
        db.add(new_item)

    # 6️⃣ Update order total
    order.total_price += product.price * quantity

    db.commit()
    db.refresh(order)

    return order



@router.get("/{order_id}/receipt")
def get_receipt(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1️⃣ Fetch the order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 2️⃣ Ensure the current user owns the order
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You are not allowed to view this receipt")

    # 3️⃣ Return receipt
    return crud.get_order_details(db, order_id)


# ---------------------------------------------------------------------------
# Seller orders — GET /api/seller/orders  and  GET /api/orders/seller
# ---------------------------------------------------------------------------

def _get_seller_orders(db: Session, current_user: User) -> list[dict]:
    if current_user.role != "seller":
        raise HTTPException(status_code=403, detail="Only sellers can view seller orders")
    shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
    if not shop:
        return []
    product_ids = [p.id for p in db.query(Product.id).filter(Product.shop_id == shop.id).all()]
    if not product_ids:
        return []
    order_ids = (
        db.query(OrderItem.order_id)
        .filter(OrderItem.product_id.in_(product_ids))
        .distinct()
        .all()
    )
    if not order_ids:
        return []
    orders = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id.in_([r.order_id for r in order_ids]))
        .order_by(Order.id.desc())
        .all()
    )
    return [_serialize_order(db, o) for o in orders]


@seller_api_router.get("/orders")
def get_seller_orders_v1(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_seller_orders(db, current_user)


# ---------------------------------------------------------------------------
# Notify-ready — POST /api/orders/{order_id}/notify-ready
# ---------------------------------------------------------------------------

class NotifyReadyBody(BaseModel):
    pickup_from: str
    pickup_to: str


def _send_resend_email(to: str, subject: str, html: str) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL", "noreply@bomnous.com")
    if not api_key:
        return
    try:
        import resend  # type: ignore
        resend.api_key = api_key
        resend.Emails.send({"from": from_email, "to": [to], "subject": subject, "html": html})
    except Exception:
        pass


def _notify_ready(order_id: int, body: NotifyReadyBody, db: Session, current_user: User) -> dict:
    if current_user.role != "seller":
        raise HTTPException(status_code=403, detail="Only sellers can mark orders as ready")
    order = db.query(Order).options(joinedload(Order.items)).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    shop = db.query(Shop).filter(Shop.owner_id == current_user.id).first()
    if shop:
        shop_product_ids = {p.id for p in db.query(Product.id).filter(Product.shop_id == shop.id).all()}
        order_product_ids = {item.product_id for item in order.items}
        if not shop_product_ids.intersection(order_product_ids):
            raise HTTPException(status_code=403, detail="This order contains no products from your shop")

    order.status = "ready"
    db.commit()
    db.refresh(order)

    buyer = db.query(User).filter(User.id == order.user_id).first()
    if buyer and buyer.email:
        html = (
            f"<p>Hi {buyer.username or 'there'},</p>"
            f"<p>Your Bomnous order <strong>#{order.id}</strong> is ready for pickup!</p>"
            f"<p><strong>Pickup window:</strong> {body.pickup_from} – {body.pickup_to}</p>"
            f"<p>Thank you for shopping on Bomnous.</p>"
        )
        _send_resend_email(buyer.email, f"Your Bomnous order #{order.id} is ready!", html)

    return {"message": "Order marked as ready", "order_id": order.id, "status": "ready"}


@api_router.post("/{order_id}/notify-ready")
def notify_order_ready(
    order_id: int,
    body: NotifyReadyBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _notify_ready(order_id, body, db, current_user)
