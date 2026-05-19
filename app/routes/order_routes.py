from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.db import get_db
from app.utils.security import get_current_user
from app.models import User, Order, Product, OrderItem, Shop
from app.schemas.product import ProductResponse
import app.crud as crud


router = APIRouter(prefix="/orders", tags=["Orders"])
api_router = APIRouter(prefix="/api/orders", tags=["Orders"])


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


@router.post("/")
def create_order(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    #  Only buyers can create orders
    if current_user.role != "buyer":
        raise HTTPException(
            status_code=403,
            detail="Only buyers can create orders"
        )

    order = crud.create_order(db, current_user.id)
    return _serialize_order(db, order)


@api_router.post("/")
def api_create_order(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "buyer":
        raise HTTPException(status_code=403, detail="Only buyers can create orders")
    order = crud.create_order(db, current_user.id)
    return _serialize_order(db, order)


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
