from sqlalchemy import (
    create_engine,
    Column, Integer,
    String, ForeignKey, Text,
    Float, Boolean, DateTime
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime as dt

Base = declarative_base()
engine = create_engine(
    os.getenv("DATABASE_URL")
)
Session = sessionmaker(bind=engine)
session = Session()


class Business(Base):
    __tablename__ = 'business'
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    address = Column(String(50))
    telephone = Column(String(20))
    email = Column(String(50), unique=True)
    latest = Column(String(100))
    category_id = Column(Integer, ForeignKey('category.id'))
    owner_id = Column(Integer, ForeignKey('user.id'))
    product = relationship("Product", back_populates="sme")
    owner = relationship("User", back_populates="sme")
    category = relationship("Category", back_populates="sme")


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    is_smeowner = Column(Boolean, default=False)
    email = Column(String(80), unique=True)
    telephone = Column(String(20))
    preference = Column(Text, default='')
    signup_date = Column(DateTime, default=dt.utcnow())
    sme = relationship("Business", uselist=False, back_populates="owner")


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    sme = relationship("Business", back_populates="category")

    @staticmethod
    def add_categories():
        cats = [
            'Clothing/Fashion', 'Hardware Accessories',
            'Food/Kitchen Ware', 'ArtnDesign', 'Other'
        ]
        print([j.name for j in session.query(Category).all()])
        for i in cats:
            if i not in [j.name for j in session.query(Category).all()]:
                new = Category(name=i)
                session.add(new)
        session.commit()
        print([j.name for j in session.query(Category).all()])


class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(Text)
    price = Column(Float)
    image = Column(String(250))
    sme_id = Column(Integer, ForeignKey('business.id'))
    sme = relationship("Business", back_populates="product")
    datecreated = Column(DateTime, default=dt.utcnow())


if __name__ == "__main__":
    Base.metadata.create_all(engine)
