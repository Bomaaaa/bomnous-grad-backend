"""Serialize Product rows for API responses (shop_name + seller_id)."""

from app.models import Product
from app.schemas.product import ProductResponse


def product_to_response(
    product: Product,
    *,
    shop_name: str | None = None,
    shop_owner_id: int | None = None,
) -> dict:
    data = ProductResponse.model_validate(product).model_dump()
    if shop_name is not None:
        data["shop_name"] = shop_name
    sid = product.seller_id
    if sid is None and shop_owner_id is not None:
        sid = shop_owner_id
    data["seller_id"] = sid
    return data
