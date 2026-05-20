from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db import SessionLocal, get_db
from app.models import Product, Shop, User
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.product_search import search_products_public
from app.product_serialize import product_to_response
from app.utils.security import get_current_user



router = APIRouter(prefix="/api/products", tags=["Products"])



# CREATE PRODUCT
@router.post("/", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db),  current_user: User = Depends(get_current_user)):

      # Role check
    if current_user.role != "seller":
        raise HTTPException(
            status_code=403,
            detail="Only sellers can create products"
        )

    # `shop_name` is response-only; ignore any unexpected fields defensively.
    payload = product.model_dump()
    payload.pop("shop_name", None)

    shop = db.query(Shop).filter(Shop.id == payload["shop_id"]).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    if shop.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only add products to your own shop")

    new_product = Product(**payload, seller_id=current_user.id)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


# GET ALL PRODUCTS
@router.get("/", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    rows = (
        db.query(Product, Shop.name.label("shop_name"), Shop.owner_id.label("owner_id"))
        .join(Shop, Product.shop_id == Shop.id)
        .order_by(Product.id)
        .all()
    )
    return [
        product_to_response(p, shop_name=shop_name, shop_owner_id=owner_id)
        for p, shop_name, owner_id in rows
    ]


@router.get("/search", response_model=list[ProductResponse])
def api_products_search(
    db: Session = Depends(get_db),
    q: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=40),
    aesthetic: str | None = Query(default=None, max_length=40),
    tag: str | None = Query(default=None, max_length=40),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    sort: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=200, ge=1, le=500),
):
    """GET /api/products/search — same filters as /products/search; q matches name, description, category, aesthetic_tag, tag."""
    return search_products_public(
        db,
        q=q,
        category=category,
        aesthetic=aesthetic,
        tag=tag,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        limit=limit,
    )


# Sellers can see only their products
@router.get("/my-products", response_model=list[ProductResponse])
def get_my_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "seller":
        raise HTTPException(
            status_code=403,
            detail="Only sellers can view their products"
        )

    rows = (
        db.query(Product, Shop.name.label("shop_name"), Shop.owner_id.label("owner_id"))
        .join(Shop, Product.shop_id == Shop.id)
        .filter(Product.seller_id == current_user.id)
        .order_by(Product.id.desc())
        .all()
    )
    return [
        product_to_response(p, shop_name=shop_name, shop_owner_id=owner_id)
        for p, shop_name, owner_id in rows
    ]


# GET PRODUCT BY ID
@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    row = (
        db.query(Product, Shop.name.label("shop_name"), Shop.owner_id.label("owner_id"))
        .join(Shop, Product.shop_id == Shop.id)
        .filter(Product.id == product_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    product, shop_name, owner_id = row
    return product_to_response(product, shop_name=shop_name, shop_owner_id=owner_id)


# UPDATE PRODUCT
@router.put("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db),  current_user: User = Depends(get_current_user)):
    existing_product = db.query(Product).filter(Product.id == product_id).first()
    if not existing_product:
        raise HTTPException(status_code=404, detail="Product not found")

    #  Only sellers can update
    if current_user.role != "seller":
        raise HTTPException(
            status_code=403,
            detail="Only sellers can update products"
        )

    # Seller must own the product
    if existing_product.seller_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to update this product"
        )

    update_data = product.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(existing_product, key, value)

    db.commit()
    db.refresh(existing_product)
    return existing_product


# DELETE PRODUCT
@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db),  current_user: User = Depends(get_current_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
      # Only sellers can delete
    if current_user.role != "seller":
        raise HTTPException(
            status_code=403,
            detail="Only sellers can delete products"
        )

    # Must own product
    if product.seller_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this product"
        )

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}


