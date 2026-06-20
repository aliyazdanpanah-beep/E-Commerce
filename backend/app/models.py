from sqlalchemy import Integer, String, Boolean, Column, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from database import Base


class Users(Base):
   __tablename__ = 'users'

   id = Column(Integer, primary_key=True, index=True)
   username = Column(String, unique=True, nullable=False)
   email = Column(String, unique=True, nullable=False)
   hashed_password = Column(String, nullable=False)
   first_name = Column(String)
   last_name = Column(String)
   role = Column(String, default="user")
   is_active = Column(Boolean, default=True)
   carts = relationship("Cart", back_populates="user", cascade="all, delete-orphan")
   products = relationship("Products", back_populates="owner")
   categories = relationship("Categorys", back_populates="owner")


class Categorys(Base):
   __tablename__ = "categorys"

   id = Column(Integer, primary_key=True, index=True)
   img = Column(String)
   title = Column(String, nullable=False)
   owner_id = Column(Integer, ForeignKey("users.id"))
   owner = relationship("Users", back_populates="categories")
   products = relationship("Products", back_populates="category_rel")


class Products(Base):
   __tablename__ = "products"

   id = Column(Integer, primary_key=True, index=True)
   name = Column(String(256), nullable=False)
   category = Column(String(256))
   price = Column(Integer, nullable=False)
   img = Column(String)
   stock = Column(Integer, default=0)
   description = Column(String, nullable=True)
   owner_id = Column(Integer, ForeignKey("users.id"))
   category_id = Column(Integer, ForeignKey("categorys.id"))  # ✅ ADD THIS   
   owner = relationship("Users", back_populates="products")
   category_rel = relationship("Categorys", back_populates="products")  # ✅ Now this works
   cart_items = relationship("CartItem", back_populates="product", cascade="all, delete-orphan")

class Cart(Base):
   __tablename__ = "carts"

   id = Column(Integer, primary_key=True, index=True)
   user_id = Column(Integer, ForeignKey("users.id"), unique=True)
   is_active = Column(Boolean, default=True)
   user = relationship("Users", back_populates="carts")
   items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
   __tablename__ = "cart_items"

   id = Column(Integer, primary_key=True, index=True)
   cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
   product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
   quantity = Column(Integer, default=1, nullable=False)
   price_at_add = Column(Float, nullable=False)
   cart = relationship("Cart", back_populates="items")
   product = relationship("Products", back_populates="cart_items")