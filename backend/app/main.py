from fastapi import FastAPI
from router import auth
from models import Base
from database import engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)