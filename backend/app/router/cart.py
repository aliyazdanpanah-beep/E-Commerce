from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Annotated, List, Optional
from starlette import status
from datetime import datetime

from database import SessionLocal
from models import Cart, CartItem, Products, Users
from .auth import get_current_user


router = APIRouter(
    prefix='/cart',
    tags=['cart']
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
    product_id: int
    quantity: int
    price_at_add: float
    subtotal: float
    # created_at: datetime
    
    class Config:
        from_attributes = True  # ✅ This replaces 'orm_mode' in newer Pydantic


class CartResponse(BaseModel):
    id: int
    user_id: int
    is_active: bool
    # created_at: datetime
    # updated_at: datetime
    items: List[CartItemResponse]
    total_items: int
    total_price: float
    
    class Config:
        from_attributes = True


class CartItemRequest(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0, default=1)


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(gt=0)


# ==================== Helper Functions ====================

def get_user_cart(db: Session, user_id: int, create_if_missing: bool = True):
    """Get or create a cart for a user"""
    cart = db.query(Cart).filter(Cart.user_id == user_id, Cart.is_active == True).first()
    
    if cart is None and create_if_missing:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    
    return cart


def calculate_cart_totals(cart: Cart):
    """Calculate total items and price for a cart"""
    total_items = 0
    total_price = 0.0
    
    for item in cart.items:
        total_items += item.quantity
        total_price += item.quantity * item.price_at_add
    
    return total_items, total_price


# ==================== Cart Endpoints ====================

@router.get('/', status_code=status.HTTP_200_OK, response_model=CartResponse)
async def get_cart(user: user_dependency, db: db_dependency):
    """Get the current user's cart"""
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    cart = get_user_cart(db, user.get('id'))
    if cart is None:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    # Calculate totals
    total_items, total_price = calculate_cart_totals(cart)
    
    # Build response items
    items_response = []
    for item in cart.items:
        items_response.append(
            CartItemResponse(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_at_add=item.price_at_add,
                subtotal=item.quantity * item.price_at_add,
                # created_at=item.created_at
            )
        )
    
    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        is_active=cart.is_active,
        # created_at=cart.created_at,
        # updated_at=cart.updated_at,
        items=items_response,
        total_items=total_items,
        total_price=total_price
    )


@router.post('/add', status_code=status.HTTP_200_OK)
async def add_to_cart(
    user: user_dependency,
    db: db_dependency,
    request: CartItemRequest
):
    """Add a product to the cart"""
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Check if product exists and has stock
    product = db.query(Products).filter(Products.id == request.product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.stock < request.quantity:
        raise HTTPException(
            status_code=400, 
            detail=f"Insufficient stock. Available: {product.stock}"
        )
    
    # Get or create cart
    cart = get_user_cart(db, user.get('id'))
    
    # Check if product already in cart
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == request.product_id
    ).first()
    
    if existing_item:
        # Update quantity
        existing_item.quantity += request.quantity
        db.commit()
        db.refresh(existing_item)
        return {
            "message": "Cart updated successfully",
            "item_id": existing_item.id,
            "product_id": existing_item.product_id,
            "quantity": existing_item.quantity,
            "price": existing_item.price_at_add,
            "subtotal": existing_item.quantity * existing_item.price_at_add
        }
    else:
        # Add new item
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
            "message": "Product added to cart successfully",
            "item_id": cart_item.id,
            "product_id": cart_item.product_id,
            "quantity": cart_item.quantity,
            "price": cart_item.price_at_add,
            "subtotal": cart_item.quantity * cart_item.price_at_add
        }


@router.put('/update/{item_id}', status_code=status.HTTP_200_OK)
async def update_cart_item(
    user: user_dependency,
    db: db_dependency,
    request: UpdateCartItemRequest,
    item_id: int = Path(gt=0)
):
    """Update quantity of a cart item"""
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get the cart item
    cart_item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if cart_item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    # Verify cart belongs to user
    cart = db.query(Cart).filter(Cart.user_id == user.get('id')).first()
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
        "item_id": cart_item.id,
        "product_id": cart_item.product_id,
        "quantity": cart_item.quantity,
        "subtotal": cart_item.quantity * cart_item.price_at_add
    }


@router.delete('/remove/{item_id}', status_code=status.HTTP_204_NO_CONTENT)
async def remove_cart_item(
    user: user_dependency,
    db: db_dependency,
    item_id: int = Path(gt=0)
):
    """Remove a specific item from cart"""
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get the cart item
    cart_item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if cart_item is None:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    # Verify cart belongs to user
    cart = db.query(Cart).filter(Cart.user_id == user.get('id')).first()
    if cart is None:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(cart_item)
    db.commit()


@router.delete('/clear', status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(user: user_dependency, db: db_dependency):
    """Clear all items from cart"""
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    cart = get_user_cart(db, user.get('id'), create_if_missing=False)
    if cart is None:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    # Delete all items
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()


@router.post('/checkout', status_code=status.HTTP_200_OK)
async def checkout(user: user_dependency, db: db_dependency):
    """Checkout - clear cart and return order summary"""
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    cart = get_user_cart(db, user.get('id'), create_if_missing=False)
    if cart is None:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Calculate totals
    total_items, total_price = calculate_cart_totals(cart)
    
    # Get items summary
    items_summary = []
    for item in cart.items:
        product = db.query(Products).filter(Products.id == item.product_id).first()
        if product:
            # Reduce stock
            product.stock -= item.quantity
            items_summary.append({
                "product_id": product.id,
                "product_name": product.name,
                "quantity": item.quantity,
                "price": item.price_at_add,
                "subtotal": item.quantity * item.price_at_add
            })
    
    # Clear the cart
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    
    return {
        "message": "Checkout successful",
        "order_summary": {
            "total_items": total_items,
            "total_price": total_price,
            "items": items_summary
        }
    }