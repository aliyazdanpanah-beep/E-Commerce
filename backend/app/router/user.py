from fastapi import APIRouter, Depends, HTTPException, Path, Query
from models import Users
from database import SessionLocal
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status
from pydantic import BaseModel, Field
from .auth import get_current_user
from passlib.context import CryptContext


router = APIRouter(
     prefix='/user',
     tags=['user']
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
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

@router.get('/', status_code=status.HTTP_200_OK)
async def get_first_user(user: user_dependency, db: db_dependency):
     if user is None:
          raise HTTPException(status_code=401, detail='Authentication Filed')
     return db.query(Users).filter(Users.id == user.get('id')).first()


@router.put('/password/{user_id}', status_code=status.HTTP_200_OK)
async def change_password(user: user_dependency, db: db_dependency, verifay: user_verfic):
     if user is None:
          raise HTTPException(status_code=401, detail='Authentication Filed')
     user_model = db.query(Users).filter(Users.id == user.get('id')).first()
     
     if not bcrypt_context.verify(verifay.password, user_model.hashed_password):
          raise HTTPException(status_code=401, detail="Error on password change")
     user_model.hashed_password = bcrypt_context.hash(verifay.new_password)
     db.add(user_model)
     db.commit()