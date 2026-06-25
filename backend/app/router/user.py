from fastapi import APIRouter, Depends, HTTPException
from models import Users
from typing import Annotated
from starlette import status
from pydantic import BaseModel, Field
from .auth import get_current_user
from dependencies import db_dependency, bcrypt_context


router = APIRouter(
     prefix='/user',
     tags=['user']
)


user_dependency = Annotated[dict, Depends(get_current_user)]


class user_verfic(BaseModel):
    password: str
    new_password: str = Field(min_length=6)

@router.get('/', status_code=status.HTTP_200_OK)
async def get_first_user(user: user_dependency, db: db_dependency):
     if user is None:
          raise HTTPException(status_code=401, detail='Authentication Failed')
     return db.query(Users).filter(Users.id == user.get('id')).first()


@router.put('/password/', status_code=status.HTTP_200_OK)
async def change_password(user: user_dependency, db: db_dependency, verifay: user_verfic):
     if user is None:
          raise HTTPException(status_code=401, detail='Authentication Failed')
     user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    
     if user_model is None:
         raise HTTPException(status_code=404, detail='User not found')
    
     if not bcrypt_context.verify(verifay.password, user_model.hashed_password):
          raise HTTPException(status_code=401, detail="Error on password change")
     user_model.hashed_password = bcrypt_context.hash(verifay.new_password)
     db.add(user_model)
     db.commit()


@router.delete('/delete/user/')
async def delete_user(user: user_dependency, db: db_dependency):
     if user is None:
          raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized')
     user_model = db.query(Users).filter(Users.id == user.get('id')).first()

     if user_model is None:
          raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='user not found')
     db.delete(user_model)
     db.commit()