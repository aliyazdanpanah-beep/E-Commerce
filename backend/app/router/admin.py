from fastapi import APIRouter, Path, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from pydantic import BaseModel, Field
from typing import Annotated
from starlette import status
import models
from models import Categorys, Products, Users
from .auth import get_current_user


router = APIRouter(
     prefix='/admin',
     tags=['admin']
)


def get_db():
     db = SessionLocal()
     try:
          yield db
     finally:
          db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class ProductRequest(BaseModel):
     name: str
     category: str
     price: int
     img: str
     stock: int
     description: str


class CategoryRequest(BaseModel):
     img: str
     title: str


@router.get('/users', status_code=status.HTTP_200_OK)
async def read_all_users(user: user_dependency, db: db_dependency):
     if user is None or user.get('user_role') != 'admin':
          raise HTTPException(status_code=401, detail="Auautherized")
     user_model = db.query(Users).all()
     return user_model


@router.get('/product', status_code=status.HTTP_200_OK)
async def read_all_users(user: user_dependency, db: db_dependency):
     if user is None or user.get('user_role') != 'admin':
          raise HTTPException(status_code=401, detail="Auautherized")
     product_model = db.query(Products).all()
     return product_model


@router.get('/categorys', status_code=status.HTTP_200_OK)
async def read_all_users(user: user_dependency, db: db_dependency):
     if user is None or user.get('user_role') != 'admin':
          raise HTTPException(status_code=401, detail="Auautherized")
     category_model = db.query(Categorys).all()
     return category_model


@router.delete('/delete/user/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user: user_dependency, db: db_dependency, user_id: int):
     if user is None or user.get('user_role') != 'admin':
          raise HTTPException(status_code=401, detail='Auautherized')
     user_model = db.query(Users).filter(Users.id == user_id).first()
     if user_model is None:
          raise HTTPException(status_code=404, detail='user not found')
     
     db.query(Users).filter(Users.id == user_id).delete()
     db.commit()


@router.delete('/delete/category/{category_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user: user_dependency, db: db_dependency, category_id: int):
     if user is None or user.get('user_role') != 'admin':
          raise HTTPException(status_code=401, detail='Auautherized')
     category_model = db.query(Categorys).filter(Categorys.id == category_id).first()
     if category_model is None:
          raise HTTPException(status_code=404, detail='category not found')
     
     db.query(Categorys).filter(Categorys.id == category_id).delete()
     db.commit()


@router.delete('/delete/product/{product_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user: user_dependency, db: db_dependency, product_id: int):
     if user is None or user.get('user_role') != 'admin':
          raise HTTPException(status_code=401, detail='Auautherized')
     product_model = db.query(Products.id == product_id).filter(Products.id == product_id).first()
     if product_model is None:
          raise HTTPException(status_code=404, detail='Product not found')
     
     db.query(Products).filter(Products.id == product_id).delete()
     db.commit()


@router.post('/create/category', status_code=status.HTTP_201_CREATED)
async def create_category(user: user_dependency, db: db_dependency, requestBody: CategoryRequest):
     if user is None or user.get('user_role') != 'admin':
          raise HTTPException(status_code=401, detail='Auautherized')
     category_model = Categorys(**requestBody.model_dump(), owner_id = user.get('id'))
     
     db.add(category_model)
     db.commit()


@router.post('/create/product', status_code=status.HTTP_201_CREATED)
async def create_product(user: user_dependency, db: db_dependency, requestBody: ProductRequest):
     if user is None or user.get('user_role') != 'admin':
          raise HTTPException(status_code=401, detail='Auautherized')
     product_model = Products(**requestBody.model_dump(), owner_id = user.get('id'))

     db.add(product_model)
     db.commit()


@router.put('/update/product/{product_id}', status_code=status.HTTP_200_OK)
async def update_category(user: user_dependency, db: db_dependency,
                           requestBody: ProductRequest, product_id: int = Path(gt=0)):
     
     if user is None or user.get('user_role') != 'admin':
          raise HTTPException(status_code=401, detail='Auautherized')
     
     product_model = db.query(Products).filter(Products.id == product_id).first()
     if product_model is None:
          raise HTTPException(status_code=401, detail='Auautherized')
     
     product_model.name = requestBody.name
     product_model.img = requestBody.img
     product_model.category = requestBody.category
     product_model.price = requestBody.price
     product_model.description = requestBody.description
     product_model.stock = requestBody.stock
     
     db.add(product_model)
     db.commit()


@router.put('/update/category/{category_id}', status_code=status.HTTP_200_OK)
async def update_category(user: user_dependency, db: db_dependency,
                           requestBody: CategoryRequest, category_id: int = Path(gt=0)):
     
     if user is None or user.get('user_role') != 'admin':
          raise HTTPException(status_code=401, detail='Auautherized')
     
     category_model = db.query(Categorys).filter(Categorys.id == category_id).first()
     if category_model is None:
          raise HTTPException(status_code=401, detail='Auautherized')
     
     category_model.img = requestBody.img
     category_model.title = requestBody.title

     db.add(category_model)
     db.commit()