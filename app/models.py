from sqlalchemy import Column, Integer, String
from .db import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, unique=True, index=True)
    room_type = Column(String)
    # available / occupied / cleaning
    status = Column(String, default="available")


class Guest(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=True)
    id_proof = Column(String, nullable=True)
    address = Column(String, nullable=True)
