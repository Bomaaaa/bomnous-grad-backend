from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.db import Base, engine
from app.routes import (
    aesthetic_routes,
    shop_routes,
    product_routes,
    order_routes,
    user_routes,
    auth_routes,
    search_routes,
    chat_routes,
    cart_routes,
    wishlist_routes,
)


load_dotenv()
app = FastAPI()


@app.on_event("startup")
def ensure_tables():
    """Create cart/wishlist tables if missing (safe no-op when they already exist)."""
    Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # We use Bearer tokens (Authorization header), not cookies.
    # Using allow_credentials=True with allow_origins=["*"] will be rejected by browsers.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Bomnous Shops Backend is running!🚀"}


app.include_router(shop_routes.router)
app.include_router(aesthetic_routes.router)
app.include_router(product_routes.router)
app.include_router(order_routes.router)
app.include_router(order_routes.api_router)
app.include_router(cart_routes.router)
app.include_router(wishlist_routes.router)
app.include_router(user_routes.router)
app.include_router(user_routes.api_router)
app.include_router(auth_routes.router)
app.include_router(search_routes.router)
app.include_router(chat_routes.router)


