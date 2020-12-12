from sqlalchemy import (
    create_engine,
    Column, Integer,
    String, ForeignKey
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
    category = relationship("Category", back_populates="smes")
    owner_id = Column(Integer, ForeignKey('smeowner.id'))


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
    smes = relationship("Business", back_populates="category")


if __name__ == "__main__":
    Base.metadata.create_all(engine)
