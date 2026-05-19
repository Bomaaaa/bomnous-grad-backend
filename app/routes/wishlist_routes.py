from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Product, Shop, User, WishlistItem
from app.schemas.product import ProductResponse
from app.schemas.wishlist import WishlistItemCreate, WishlistItemResponse
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/wishlist", tags=["Wishlist"])


def _product_response(db: Session, product: Product) -> ProductResponse:
    shop_name = db.query(Shop.name).filter(Shop.id == product.shop_id).scalar()
    data = ProductResponse.model_validate(product).model_dump()
    data["shop_name"] = shop_name
    return ProductResponse(**data)


def _wishlist_item_response(db: Session, row: WishlistItem) -> WishlistItemResponse:
    product = db.query(Product).filter(Product.id == row.product_id).first()
    return WishlistItemResponse(
        id=row.id,
        product_id=row.product_id,
        product=_product_response(db, product) if product else None,
    )


@router.get("/", response_model=list[WishlistItemResponse])
def list_wishlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(WishlistItem)
        .filter(WishlistItem.user_id == current_user.id)
        .order_by(WishlistItem.id.desc())
        .all()
    )
    return [_wishlist_item_response(db, row) for row in rows]


@router.post("/", response_model=WishlistItemResponse)
def add_to_wishlist(
    body: WishlistItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == body.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing = (
        db.query(WishlistItem)
        .filter(
            WishlistItem.user_id == current_user.id,
            WishlistItem.product_id == body.product_id,
        )
        .first()
    )
    if existing:
        return _wishlist_item_response(db, existing)

    row = WishlistItem(user_id=current_user.id, product_id=body.product_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _wishlist_item_response(db, row)


@router.delete("/{wishlist_item_id}")
def remove_wishlist_item(
    wishlist_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(WishlistItem)
        .filter(WishlistItem.id == wishlist_item_id, WishlistItem.user_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    db.delete(row)
    db.commit()
    return {"message": "Removed from wishlist"}
