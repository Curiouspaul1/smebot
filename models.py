from sqlalchemy import (
    create_engine,
    Column, Integer,
    String, ForeignKey, Text,
    Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
Base = declarative_base()
engine = create_engine(
    "sqlite:////home/paul/Documents/projects/smebot/dev.db"
)


class Business(Base):
    __tablename__ = 'business'
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    address = Column(String(50))
    telephone = Column(String(20))
    email = Column(String(50), unique=True)
    category_id = Column(Integer, ForeignKey('category.id'))
    owner_id = Column(Integer, ForeignKey('smeowner.id'))
    product = relationship("Product", back_populates="sme")
    owner = relationship("SmeOwner", back_populates="sme")
    category = relationship("Category", back_populates="sme")


class Customer(Base):
    __tablename__ = 'customer'
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    email = Column(String(50), unique=True)
    telephone = Column(String(20))
    preference = Column(String(50))


class SmeOwner(Base):
    __tablename__ = 'smeowner'
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    email = Column(String(50), unique=True)
    telephone = Column(String(20))
    sme = relationship("Business", uselist=False, back_populates="owner")


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    sme = relationship("Business", back_populates="category")


class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    description = Column(Text)
    price = Column(Float)
    sme_id = Column(Integer, ForeignKey('business.id'))
    sme = relationship("Business", back_populates="product")


if __name__ == "__main__":
    Base.metadata.create_all(engine)
