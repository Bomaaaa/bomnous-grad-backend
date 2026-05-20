#!/usr/bin/env python3
"""
seed_bomnous.py — Bomnous Graduation Project (Near East University 2026)

Seeds 17 real North Cyprus shops + seller accounts + 85 products.
Uses the same SQLAlchemy models as the FastAPI backend (integer IDs, hashed_password, etc.).

Usage (from bomnous-grad-backend/):
    export DATABASE_URL=postgresql://...   # or set in .env
    python seed_bomnous.py
    python seed_bomnous.py --force         # add missing rows even if partially seeded

All seller logins: email from SHOPS below, password Bomnous2026!
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from passlib.context import CryptContext  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import Product, Shop, User  # noqa: E402

SELLER_PASSWORD = "Bomnous2026!"
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Same algorithm as app.utils.security — avoids needing JWT env vars for seed."""
    return _pwd_context.hash(password[:72])
MARKER_SHOP = "Garderobe"

TAGS = ("trending", "just-dropped", "editors-picks")
AESTHETIC_BY_CATEGORY = {
    "women": "soft-luxury",
    "men": "smart-casual",
    "baby": "everyday",
}

# ── Shop + seller definitions ─────────────────────────────────────────────────

SHOPS = [
    {
        "name": "Garderobe",
        "city": "Lefkoşa",
        "address": "Şht. Aziz Güner Sk, Ortaköy, Lefkoşa",
        "phone": "+90 392 228 83 66",
        "category": "women",
        "instagram": None,
        "description": "Elegant evening dresses, jewellery and accessories in the heart of Ortaköy. Known for stunning gowns and a warm personal service — the owner even hand-delivers orders.",
        "email": "garderobe.lefkosa@bomnous.com",
    },
    {
        "name": "Stylish Boutique",
        "city": "Lefkoşa",
        "address": "Şehit Kemal Ünal Caddesi, Kızılay, Lefkoşa",
        "phone": "+90 533 868 69 35",
        "category": "women",
        "instagram": None,
        "description": "Curated women's fashion in central Lefkoşa. Seasonal collections, everyday wear and special-occasion pieces at accessible prices.",
        "email": "stylish.lefkosa@bomnous.com",
    },
    {
        "name": "Nera Boutique",
        "city": "Girne",
        "address": "Canbulat Sk, Girne",
        "phone": "+90 533 822 82 28",
        "category": "women",
        "instagram": None,
        "description": "Girne's most-loved boutique. Genuine leather bags, sunglasses, jewellery and accessories. Open every day — a must-visit on the harbour strip.",
        "email": "nera.girne@bomnous.com",
    },
    {
        "name": "NOVITA Girne",
        "city": "Girne",
        "address": "Nelly Court, Semih Sancar Caddesi No:6, Girne",
        "phone": "+90 533 838 96 08",
        "category": "women",
        "instagram": "novitafashion.shop",
        "description": "Contemporary women's fashion with its own online shop. Seasonal drops, modern silhouettes and trend-forward pieces for the Girne woman.",
        "email": "novita.girne@bomnous.com",
    },
    {
        "name": "LUNA Fashion",
        "city": "Gazimağusa",
        "address": "İsmet İnönü Blvd, Gazimağusa",
        "phone": "+90 533 831 17 77",
        "category": "women",
        "instagram": None,
        "description": "Popular women's fashion store on Famagusta's main boulevard. Ships island-wide — orders from Nicosia arrive faster than local shops. Clothes match the photos, always.",
        "email": "luna.magusa@bomnous.com",
    },
    {
        "name": "Purple Rain Famagusta",
        "city": "Gazimağusa",
        "address": "Şafak Plaza, Cahit Sıtkı Tarancı Sokak No:1, Gazimağusa",
        "phone": "+90 392 365 20 05",
        "category": "women",
        "instagram": None,
        "description": "Boutique evening gowns in a wide spectrum of colours. Welcoming to everyone regardless of size or background. Customisation available. English-speaking owner.",
        "email": "purplerain.magusa@bomnous.com",
    },
    {
        "name": "Aysan Butik",
        "city": "Güzelyurt",
        "address": "Erol Reşat Sk 2/B, Güzelyurt",
        "phone": "+90 392 714 23 81",
        "category": "women",
        "instagram": None,
        "description": "A charming discovery in Güzelyurt's town centre. Quality women's clothing at fair prices — a hidden gem in North Cyprus's citrus capital.",
        "email": "aysan.guzelyurt@bomnous.com",
    },
    {
        "name": "Baddie Butik",
        "city": "Güzelyurt",
        "address": "Ecevit Caddesi 38, Güzelyurt",
        "phone": "+90 533 882 06 19",
        "category": "women",
        "instagram": "baddiebutik.com",
        "description": "Trendy women's clothing and shoes with its own website. Loyal local following, new arrivals weekly. Open 7 days a week.",
        "email": "baddie.guzelyurt@bomnous.com",
    },
    {
        "name": "Rengarenk",
        "city": "İskele",
        "address": "Şehit İlker Kartel Caddesi, Sayılı İş Merkezi, İskele",
        "phone": "+90 392 371 23 39",
        "category": "women",
        "instagram": None,
        "description": "İskele's most-reviewed clothing store. Wide selection of women's and children's wear, accessories, pyjamas and homewear. Friendly staff, affordable prices.",
        "email": "rengarenk.iskele@bomnous.com",
    },
    {
        "name": "L'uomo Menswear",
        "city": "Lefkoşa",
        "address": "Αρχιεπισκόπου Μακαρίου Γ' 2, Lefkoşa",
        "phone": "+357 22 676520",
        "category": "men",
        "instagram": "luomo_menswear",
        "description": "The go-to men's suit destination in Nicosia. Excellent quality suits, shirts, ties and accessories at very fair prices. Fast alterations available in-store.",
        "email": "luomo.lefkosa@bomnous.com",
    },
    {
        "name": "Baron's Sillage",
        "city": "Lefkoşa",
        "address": "Belediye Blvd, Dereli Ömer Apt No:5B, Gönyeli, Lefkoşa",
        "phone": "+90 548 855 98 32",
        "category": "men",
        "instagram": None,
        "description": "North Cyprus's most-reviewed menswear boutique. Carefully selected suits, shirts and streetwear. Staff give honest styling advice — they listen before they sell.",
        "email": "barons.lefkosa@bomnous.com",
    },
    {
        "name": "Adamax Girne",
        "city": "Girne",
        "address": "Mete Adanır Caddesi 1, Girne",
        "phone": "+90 533 876 86 68",
        "category": "men",
        "instagram": None,
        "description": "Girne's quality address for men's and women's fashion. Spacious store, great variety of trendy and classic pieces. Open late — until 8 PM daily.",
        "email": "adamax.girne@bomnous.com",
    },
    {
        "name": "Moustache Butik",
        "city": "Gazimağusa",
        "address": "İsmet İnönü Blvd, Gazimağusa",
        "phone": "+90 533 848 73 93",
        "category": "men",
        "instagram": "moustachemenwear",
        "description": "Famagusta's dedicated men's fashion destination. High-quality durable jeans, Stone Island, snapbacks and branded items. Staff have great fashion sense.",
        "email": "moustache.magusa@bomnous.com",
    },
    {
        "name": "Men & Men",
        "city": "Gazimağusa",
        "address": "İstiklal Caddesi, Gazimağusa",
        "phone": "+90 548 860 10 04",
        "category": "men",
        "instagram": None,
        "description": "Top-notch men's suits and formal wear. Owner is a 'complete gentleman' according to regulars. Opens early at 8 AM — ideal before lectures.",
        "email": "menandmen.magusa@bomnous.com",
    },
    {
        "name": "Babyli Bebek",
        "city": "Lefkoşa",
        "address": "Metropol yolu üzeri (Vakıflar Bankası yanı), Lefkoşa",
        "phone": "+90 533 831 22 29",
        "category": "baby",
        "instagram": None,
        "description": "Baby and children's clothing and accessories store in central Lefkoşa. Open 7 days, early hours. Everything a new parent needs under one roof.",
        "email": "babyli.lefkosa@bomnous.com",
    },
    {
        "name": "Mamatoto Nicosia",
        "city": "Lefkoşa",
        "address": "Andrea Michalakopoulou 15, Lefkoşa",
        "phone": "+357 22 761159",
        "category": "baby",
        "instagram": None,
        "description": "Comprehensive baby store with a wide range of clothing, gear and nursery products. Ships island-wide. Recommended by expecting parents across Cyprus.",
        "email": "mamatoto.lefkosa@bomnous.com",
    },
    {
        "name": "Mio Doro Kids",
        "city": "Girne",
        "address": "Semih Sancar Caddesi, Girne",
        "phone": "+90 548 861 19 65",
        "category": "baby",
        "instagram": None,
        "description": "Beautiful organic cotton baby and children's clothing in Girne. Lovely options for both boys and girls. Sweet, friendly owner who genuinely cares about quality.",
        "email": "miodoro.girne@bomnous.com",
    },
]

PRODUCTS_BY_CATEGORY = {
    "women": [
        ("Floral Midi Dress", "Light chiffon midi dress with a delicate floral print. Perfect for summer evenings.", 35.00, 20),
        ("High-Waist Linen Trousers", "Breathable linen trousers in sand beige. Relaxed fit, elasticated waistband.", 28.00, 15),
        ("Satin Wrap Blouse", "Elegant satin wrap-style blouse in deep burgundy. Pairs with trousers or a skirt.", 22.00, 18),
        ("Leather Crossbody Bag", "Genuine leather crossbody bag with adjustable strap. Available in black and tan.", 55.00, 10),
        ("Strappy Heeled Sandals", "Block-heel strappy sandals in nude. Comfortable for long evenings out.", 40.00, 12),
    ],
    "men": [
        ("Slim Fit Suit — Navy", "Two-piece slim fit suit in navy blue. Ideal for formal events, graduations and weddings.", 120.00, 8),
        ("Oxford Button-Down Shirt", "Classic white Oxford cotton shirt. Slim fit, double cuff. Works formal or casual.", 30.00, 25),
        ("Slim Chino Trousers", "Stretch slim chino in stone. Smart-casual staple for lectures and meetings.", 35.00, 20),
        ("Leather Belt — Brown", "Full-grain leather belt with a brushed silver buckle. Fits waist 28–42\".", 18.00, 30),
        ("Snapback Cap — Black", "Structured snapback in all-black. Adjustable strap, one size fits all.", 15.00, 40),
    ],
    "baby": [
        ("Organic Cotton Onesie Set (3-pack)", "Soft 100% organic cotton onesies in pastel tones. Sizes 0–18 months.", 22.00, 30),
        ("Knitted Baby Cardigan", "Hand-finished knitted cardigan in cream. Button front, warm and gentle on skin.", 18.00, 20),
        ("Baby Girl Tutu Dress", "Layered tulle tutu dress in soft pink. Perfect for first birthday photos.", 25.00, 15),
        ("Baby Boy Denim Dungarees", "Soft stretch denim dungarees with snap buttons. Sizes 3–24 months.", 20.00, 18),
        ("Muslin Swaddle Blankets (2-pack)", "100% cotton muslin swaddle blankets. Breathable, large size 120×120cm.", 16.00, 35),
    ],
}

IMAGE_URLS = {
    "women": [
        "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1594938298603-c8148c4b4f7d?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1592669241067-2a12e768cb9f?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=900&auto=format&fit=crop",
    ],
    "men": [
        "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=900&auto=format&fit=crop",
    ],
    "baby": [
        "https://images.unsplash.com/photo-1522771930-78848d9293e8?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1584839404765-34c0b3d5a9fa?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1515488042361-ee00e0ddd4e4?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1551044564-0bd98bcab7e7?w=900&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1519689680058-324335c77eba?w=900&auto=format&fit=crop",
    ],
}


def username_from_email(email: str) -> str:
    base = email.split("@")[0].lower()
    base = re.sub(r"[^a-z0-9_]", "_", base)
    return base[:48] or "seller"


def shop_location(city: str, address: str) -> str:
    return f"{city} — {address}"


def shop_bio(instagram: str | None) -> str | None:
    if not instagram:
        return None
    handle = instagram.replace("https://", "").replace("instagram.com/", "").strip("/")
    return f"Instagram: @{handle}"


def get_or_create_user(db: Session, shop_def: dict, pw_hash: str) -> User:
    user = db.query(User).filter(User.email == shop_def["email"]).first()
    if user:
        user.role = "seller"
        user.full_name = user.full_name or f"{shop_def['name']} Owner"
        user.city = user.city or shop_def["city"]
        user.phone = user.phone or shop_def["phone"]
        if shop_def.get("instagram"):
            user.bio = user.bio or shop_bio(shop_def["instagram"])
        return user

    username = username_from_email(shop_def["email"])
    if db.query(User).filter(User.username == username).first():
        username = f"{username}_{shop_def['city'][:3].lower()}"

    user = User(
        username=username,
        email=shop_def["email"],
        hashed_password=pw_hash,
        role="seller",
        full_name=f"{shop_def['name']} Owner",
        phone=shop_def["phone"],
        city=shop_def["city"],
        bio=shop_bio(shop_def.get("instagram")),
    )
    db.add(user)
    db.flush()
    return user


def get_or_create_shop(db: Session, shop_def: dict, owner: User) -> Shop:
    shop = db.query(Shop).filter(Shop.owner_id == owner.id).first()
    if shop:
        shop.name = shop.name or shop_def["name"]
        shop.location = shop.location or shop_location(shop_def["city"], shop_def["address"])
        shop.description = shop.description or shop_def["description"]
        shop.phone = shop.phone or shop_def["phone"]
        shop.whatsapp = shop.whatsapp or shop_def["phone"]
        shop.categories = shop.categories or json.dumps([shop_def["category"]])
        return shop

    shop = Shop(
        name=shop_def["name"],
        location=shop_location(shop_def["city"], shop_def["address"]),
        description=shop_def["description"],
        phone=shop_def["phone"],
        whatsapp=shop_def["phone"],
        categories=json.dumps([shop_def["category"]]),
        owner_id=owner.id,
    )
    db.add(shop)
    db.flush()
    return shop


def seed_products_for_shop(db: Session, shop: Shop, seller: User, cat: str, force: bool) -> int:
    existing_names = {
        p.name
        for p in db.query(Product).filter(Product.shop_id == shop.id).all()
    }
    created = 0
    images = IMAGE_URLS[cat]
    aesthetic = AESTHETIC_BY_CATEGORY[cat]

    for i, (p_name, p_desc, price, stock) in enumerate(PRODUCTS_BY_CATEGORY[cat]):
        if p_name in existing_names and not force:
            continue
        img = images[i % len(images)]
        hover = images[(i + 1) % len(images)]
        product = Product(
            name=p_name,
            description=p_desc,
            price=float(price),
            stock=int(stock),
            category=cat,
            tag=TAGS[i % len(TAGS)],
            aesthetic_tag=aesthetic,
            image_url=img,
            image_hover_url=hover if hover != img else None,
            compare_at_price=round(float(price) * 1.12, 2),
            shop_id=shop.id,
            seller_id=seller.id,
        )
        db.add(product)
        created += 1
    return created


def seed(db: Session, force: bool = False) -> None:
    if db.query(Shop).filter(Shop.name == MARKER_SHOP).first() and not force:
        print(f"Seed skipped: '{MARKER_SHOP}' already exists. Run with --force to fill missing sellers/shops/products.")
        return

    pw_hash = hash_password(SELLER_PASSWORD)
    users_created = shops_created = products_created = 0

    print("Starting Bomnous NC seed (17 shops, 85 products)...")

    for shop_def in SHOPS:
        before_users = db.query(User).filter(User.email == shop_def["email"]).count()
        user = get_or_create_user(db, shop_def, pw_hash)
        if before_users == 0:
            users_created += 1

        before_shops = db.query(Shop).filter(Shop.owner_id == user.id).count()
        shop = get_or_create_shop(db, shop_def, user)
        if before_shops == 0:
            shops_created += 1

        n = seed_products_for_shop(db, shop, user, shop_def["category"], force)
        products_created += n

    db.commit()

    total_users = db.query(User).filter(User.role == "seller").count()
    total_shops = db.query(Shop).count()
    total_products = db.query(Product).count()

    print("\nSeed complete!")
    print(f"  New sellers this run : {users_created}")
    print(f"  New shops this run   : {shops_created}")
    print(f"  New products this run: {products_created}")
    print(f"  Total sellers in DB  : {total_users}")
    print(f"  Total shops in DB    : {total_shops}")
    print(f"  Total products in DB : {total_products}")
    print(f"\n  Seller password for all seeded accounts: {SELLER_PASSWORD}")
    print("\n  Shops by city:")
    cities: dict[str, list[str]] = {}
    for s in SHOPS:
        cities.setdefault(s["city"], []).append(s["name"])
    for city, names in sorted(cities.items()):
        print(f"    {city}: {', '.join(names)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Bomnous North Cyprus shops")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Do not skip when Garderobe exists; add any missing users/shops/products",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        seed(db, force=args.force)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
