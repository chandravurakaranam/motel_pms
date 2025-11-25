from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from .db import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    # 👉 keep this name: number
    number = Column(String, unique=True, index=True)
    room_type = Column(String)
    status = Column(String, default="available")

    # optional, only if you added it:
    # reservations = relationship("Reservation", back_populates="room")


class Guest(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=True)
    id_proof = Column(String, nullable=True)
    address = Column(String, nullable=True)

    # reservations = relationship("Reservation", back_populates="guest")


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    guest_id = Column(Integer, ForeignKey("guests.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    check_in = Column(Date)
    check_out = Column(Date)
    notes = Column(String, nullable=True)
    status = Column(String, default="booked")

    guest = relationship("Guest")
    room = relationship("Room")
