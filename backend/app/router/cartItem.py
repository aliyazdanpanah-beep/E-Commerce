from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Annotated
from starlette import status
from datetime import datetime

from database import SessionLocal
from models import Cart, CartItem, Products
from .auth import get_current_user


router = APIRouter(
    prefix='/cart/items',
    tags=['cart_items']
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# ==================== Pydantic Models ====================

class CartItemResponse(BaseModel):
    id: int
    cart_id: int
    product_id: int
    quantity: int
    price_at_add: float
    subtotal: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(gt=0, description="New quantity")


class CartItemRequest(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, default=1)


# ==================== Helper Functions ====================

def create_cart_item_response(item: CartItem) -> CartItemResponse:
    """Helper function to create CartItemResponse from CartItem model"""
    return CartItemResponse(
        id=item.id,
        cart_id=item.cart_id,
        product_id=item.product_id,
        quantity=item.quantity,
        price_at_add=item.price_at_add,
        subtotal=item.quantity * item.price_at_add,
        created_at=item.created_at
    )


def verify_cart_ownership(db: Session, cart_item_id: int, user_id: int):
    """Verify that a cart item belongs to the current user"""
    cart_item = db.query(CartItem).filter(CartItem.id == cart_item_id).first()
    if cart_item is None:
        return None, None
    
    cart = db.query(Cart).filter(Cart.id == cart_item.cart_id, Cart.user_id == user_id).first()
    return cart_item, cart


# ==================== Cart Item Endpoints ====================

@router.get('/{item_id}', status_code=status.HTTP_200_OK, response_model=CartItemResponse)
async def get_cart_item(
    user: user_dependency,
    db: db_dependency,
    item_id: int = Path(gt=0)
):
    """Get a specific cart item"""
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    cart_item, cart = verify_cart_ownership(db, item_id, user.get('id'))
    
    if cart_item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    if cart is None:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return create_cart_item_response(cart_item)


@router.put('/{item_id}', status_code=status.HTTP_200_OK)
async def update_cart_item(
    user: user_dependency,
    db: db_dependency,
    request: UpdateCartItemRequest,
    item_id: int = Path(gt=0)
):
    """Update quantity of a cart item"""
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    cart_item, cart = verify_cart_ownership(db, item_id, user.get('id'))
    
    if cart_item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    if cart is None:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check product stock
    product = db.query(Products).filter(Products.id == cart_item.product_id).first()
    if product and product.stock < request.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {product.stock}"
        )
    
    # Update quantity
    cart_item.quantity = request.quantity
    db.commit()
    db.refresh(cart_item)
    
    return {
        "message": "Cart item updated successfully",
        "item": create_cart_item_response(cart_item)
    }


@router.delete('/{item_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_cart_item(
    user: user_dependency,
    db: db_dependency,
    item_id: int = Path(gt=0)
):
    """Delete a specific cart item"""
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    cart_item, cart = verify_cart_ownership(db, item_id, user.get('id'))
    
    if cart_item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    if cart is None:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(cart_item)
    db.commit()


@router.post('/add', status_code=status.HTTP_200_OK)
async def add_item_to_cart(
    user: user_dependency,
    db: db_dependency,
    request: CartItemRequest
):
    """Add a new item to cart (standalone endpoint)"""
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Check if product exists
    product = db.query(Products).filter(Products.id == request.product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.stock < request.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {product.stock}"
        )
    
    # Get user's cart
    from .cart import get_user_cart
    cart = get_user_cart(db, user.get('id'))
    
    # Check if product already in cart
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == request.product_id
    ).first()
    
    if existing_item:
        existing_item.quantity += request.quantity
        db.commit()
        db.refresh(existing_item)
        return {
            "message": "Item quantity updated",
            "item": create_cart_item_response(existing_item)
        }
    
    # Create new cart item
    cart_item = CartItem(
        cart_id=cart.id,
        product_id=request.product_id,
        quantity=request.quantity,
        price_at_add=float(product.price)
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    
    return {
        "message": "Item added to cart successfully",
        "item": create_cart_item_response(cart_item)
    }