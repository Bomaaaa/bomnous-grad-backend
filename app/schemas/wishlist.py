from pydantic import BaseModel

from app.schemas.product import ProductResponse


class WishlistItemCreate(BaseModel):
    product_id: int


class WishlistItemResponse(BaseModel):
    id: int
    product_id: int
    product: ProductResponse | None = None

    class Config:
        from_attributes = True
