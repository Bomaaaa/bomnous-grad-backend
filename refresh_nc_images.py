#!/usr/bin/env python3
"""
Refresh product images for North Cyprus seeded shops (@bomnous.com sellers).

Uses curated Unsplash fashion photos (free to use). Safe to re-run.

  cd ~/bomnous-grad-backend
  conda activate bomnous-ai-shop
  export DATABASE_URL="postgresql://..."   # Railway public URL
  python refresh_nc_images.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from sqlalchemy.orm import Session  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import Product, Shop, User  # noqa: E402

# Product name → realistic image (Unsplash)
NC_PRODUCT_IMAGES: dict[str, tuple[str, str | None]] = {
    "Floral Midi Dress": (
        "https://images.unsplash.com/photo-1595777457583-95e059a59a09?w=900&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=900&auto=format&fit=crop&q=80",
    ),
    "High-Waist Linen Trousers": (
        "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=900&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=900&auto=format&fit=crop&q=80",
    ),
    "Satin Wrap Blouse": (
        "https://images.unsplash.com/photo-1564257631407-3deb25e9c8e0?w=900&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1583496668160-f28b07f3d8b0?w=900&auto=format&fit=crop&q=80",
    ),
    "Leather Crossbody Bag": (
        "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=900&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1590874103328-eac38a683690?w=900&auto=format&fit=crop&q=80",
    ),
    "Strappy Heeled Sandals": (
        "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=900&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1460353581641-37baddab0fa2?w=900&auto=format&fit=crop&q=80",
    ),
    "Slim Fit Suit — Navy": (
        "https://images.unsplash.com/photo-1594938298603-c8148c4b4f7d?w=900&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1617137968427-85924c2a5504?w=900&auto=format&fit=crop&q=80",
    ),
    "Oxford Button-Down Shirt": (
        "https://images.unsplash.com/photo-1602810318383-e386cc2a3f06?w=900&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=900&auto=format&fit=crop&q=80",
    ),
    "Slim Chino Trousers": (
        "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=900&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=900&auto=format&fit=crop&q=80",
    ),
    "Leather Belt — Brown": (
        "https://images.unsplash.com/photo-1624222247344-550fb60583c9?w=900&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=900&auto=format&fit=crop&q=80",
    ),
    "Snapback Cap — Black": (
        "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=900&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1521369908759-4154c4eaeaa0?w=900&auto=format&fit=crop&q=80",
    ),
    "Organic Cotton Onesie Set (3-pack)": (
        "https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?w=900&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1522771930-78848d9293e8?w=900&auto=format&fit=crop&q=80",
    ),
    "Knitted Baby Cardigan": (
        "https://images.unsplash.com/photo-1519689680058-324335c77eba?w=900&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1584839404765-34c0b3d5a9fa?w=900&auto=format&fit=crop&q=80",
    ),
    "Baby Girl Tutu Dress": (
        "https://images.unsplash.com/photo-1551044564-0bd98bcab7e7?w=900&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1503454537845-731fe8a7a238?w=900&auto=format&fit=crop&q=80",
    ),
    "Baby Boy Denim Dungarees": (
        "https://images.unsplash.com/photo-1519238263530-4422f829fb64?w=900&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1503944583229-2888feec1c8e?w=900&auto=format&fit=crop&q=80",
    ),
    "Muslin Swaddle Blankets (2-pack)": (
        "https://images.unsplash.com/photo-1586105251261-72a75633a4e5?w=900&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1522771930-78848d9293e8?w=900&auto=format&fit=crop&q=80",
    ),
}


def refresh(db: Session) -> int:
    nc_shop_ids = {
        row[0]
        for row in db.query(Shop.id)
        .join(User, Shop.owner_id == User.id)
        .filter(User.email.like("%@bomnous.com"))
        .all()
    }
    if not nc_shop_ids:
        print("No NC shops found (@bomnous.com). Updating by product name only.")

    updated = 0
    q = db.query(Product)
    if nc_shop_ids:
        q = q.filter(Product.shop_id.in_(nc_shop_ids))
    products = q.all()

    for p in products:
        urls = NC_PRODUCT_IMAGES.get(p.name)
        if not urls:
            continue
        p.image_url = urls[0]
        p.image_hover_url = urls[1]
        updated += 1

    db.commit()
    return updated


def main() -> None:
    db = SessionLocal()
    try:
        n = refresh(db)
        print(f"Updated {n} product image(s) with realistic Unsplash photos.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
