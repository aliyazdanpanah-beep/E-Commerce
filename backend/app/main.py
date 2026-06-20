from fastapi import FastAPI
from router import auth, admin, user, product, cart
from models import Base
from database import engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(product.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(user.router)
app.include_router(cart.router)