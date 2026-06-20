from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from typing import Annotated
from starlette import status
from models import Categorys, Products, Users


router = APIRouter()


def get_db():
     db = SessionLocal()
     try:
          yield db
     finally:
          db.close()

db_dependency = Annotated[Session, Depends(get_db)]


@router.get('/product', status_code=status.HTTP_200_OK)
async def get_all_product(db: db_dependency):
     return db.query(Products).all()

@router.get('/category', status_code=status.HTTP_200_OK)
async def get_all_category(db: db_dependency):
     return db.query(Categorys).all()