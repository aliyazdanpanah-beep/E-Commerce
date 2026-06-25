from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from models import Users
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from starlette import status
from datetime import timedelta, timezone, datetime
from jose import jwt, JWTError
from dependencies import db_dependency, bcrypt_context


router = APIRouter(
     prefix='/auth',
     tags=['auth']
)

SECRET_KEY = "547582j75345hg53ecj3875646k46fg36jh456753"
ALGORITHM = "HS256"

oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


class CreateUserRequest(BaseModel):
     username: str = Field(max_length=200)
     email: str = Field(max_length=200)
     first_name: str = Field(max_length=72)
     last_name: str = Field(max_length=72)
     password: str = Field(max_length=72)
     role: str = Field(max_length=72)


class Token(BaseModel):
     access_token: str
     token_type: str


# db_dependency = Annotated[Session, Depends(get_db)]


def Authenticate_user(username: str, password: str, db):
     user = db.query(Users).filter(Users.username == username).first()
     if not user:
          return False
     if not bcrypt_context.verify(password, user.hashed_password):
          return False
     return user


def create_access_token(username: str, user_id: int, role: str, expires_delta: timedelta):

     endcode = {'sub': username, 'id': user_id, 'role': role}
     expires = datetime.now(timezone.utc) + expires_delta
     endcode.update({'exp': expires})

     return jwt.encode(endcode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
     try:
          paylode = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
          username: str = paylode.get('sub')
          user_id: int = paylode.get('id')
          user_role: str = paylode.get('role')
          if username is None or user_id is None:
               raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                   detail='could not valid user')
          return {'username': username, 'id': user_id, 'user_role': user_role}
     except JWTError:
          raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                              detail="could not valid user")


@router.get('/users')
async def Get_Users(db: db_dependency):
     return db.query(Users).all()


@router.post('/create/users', status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, request_model: CreateUserRequest):
     create_user_model = Users(
          username = request_model.username,
          first_name = request_model.first_name,
          last_name = request_model.last_name,
          email = request_model.email,
          role = request_model.role,
          hashed_password = bcrypt_context.hash(request_model.password),
          is_active = True
     )

     db.add(create_user_model)
     db.commit()


@router.post('/token', response_model=Token)
async def login_for_access_token(form_date: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
     user = Authenticate_user(form_date.username, form_date.password, db)
     if not user:
          raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                              detail='Could not valid user')
     
     token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))
     return {'access_token': token, 'token_type': 'bearer'}