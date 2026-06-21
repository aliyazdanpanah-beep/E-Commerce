from fastapi import APIRouter, Depends, HTTPException, Path, Query
from models import Cart
from database import SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status
from pydantic import BaseModel, Field
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


class user_verfic(BaseModel):
     password: str
     new_password: str = Field(min_length=6)
  

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get('/', status_code=status.HTTP_200_OK)
async def all_in_user_cart(user: user_dependency, db: db_dependency):
     if user is None:
          raise HTTPException(status_code=401, detail='Aunautherizes')
     cart_model = db.query(Cart).filter(Cart.id == user.get('id'))
     return cart_model