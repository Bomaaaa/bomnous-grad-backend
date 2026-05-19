from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import CartItem, Order, OrderItem, Product, Shop, User
from app.schemas.cart import CartItemCreate, CartItemResponse
from app.schemas.product import ProductResponse
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/cart", tags=["Cart"])


def _product_response(db: Session, product: Product) -> ProductResponse:
    shop_name = db.query(Shop.name).filter(Shop.id == product.shop_id).scalar()
    data = ProductResponse.model_validate(product).model_dump()
    data["shop_name"] = shop_name
    return ProductResponse(**data)


def _cart_item_response(db: Session, row: CartItem) -> CartItemResponse:
    product = db.query(Product).filter(Product.id == row.product_id).first()
    return CartItemResponse(
        id=row.id,
        product_id=row.product_id,
        quantity=row.quantity,
        product=_product_response(db, product) if product else None,
    )


@router.get("/", response_model=list[CartItemResponse])
def list_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id)
        .order_by(CartItem.id.desc())
        .all()
    )
    return [_cart_item_response(db, row) for row in rows]


@router.post("/", response_model=CartItemResponse)
def add_to_cart(
    body: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == body.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id, CartItem.product_id == body.product_id)
        .first()
    )
    if existing:
        existing.quantity += body.quantity
        db.commit()
        db.refresh(existing)
        return _cart_item_response(db, existing)

    row = CartItem(
        user_id=current_user.id,
        product_id=body.product_id,
        quantity=body.quantity,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _cart_item_response(db, row)


@router.delete("/{cart_item_id}")
def remove_cart_item(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(CartItem)
        .filter(CartItem.id == cart_item_id, CartItem.user_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(row)
    db.commit()
    return {"message": "Removed from cart"}


@router.post("/checkout")
def checkout_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "buyer":
        raise HTTPException(status_code=403, detail="Only buyers can create orders")

    cart_rows = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_rows:
        raise HTTPException(status_code=400, detail="Cart is empty")

    order = Order(user_id=current_user.id, status="pending", total_price=0.0)
    db.add(order)
    db.flush()

    total = 0.0
    for row in cart_rows:
        product = db.query(Product).filter(Product.id == row.product_id).first()
        if not product:
            continue
        qty = row.quantity
        if product.stock < qty:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {product.name}",
            )
        product.stock -= qty
        db.add(
            OrderItem(order_id=order.id, product_id=product.id, quantity=qty),
        )
        total += product.price * qty

    order.total_price = total
    for row in cart_rows:
        db.delete(row)

    db.commit()
    db.refresh(order)
    return {
        "id": order.id,
        "status": order.status,
        "total": order.total_price,
        "total_price": order.total_price,
        "created_at": None,
        "items": [],
    }
