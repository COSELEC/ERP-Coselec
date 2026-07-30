from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

chatroom_members = Table(
    "chatroom_members",
    Base.metadata,
    Column("room_id", Integer, ForeignKey("chatrooms.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("joined_at", DateTime(timezone=True), server_default=func.now())
)

class ChatRoom(Base):
    __tablename__ = "chatrooms"
    
    id = Column(Integer, primary_key=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    is_group = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("Message", back_populates="room", cascade="all, delete-orphan")
    members = relationship("User", secondary=chatroom_members, backref="chatrooms")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    
    room_id = Column(Integer, ForeignKey("chatrooms.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    text = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    file_url = Column(String, nullable=True)
    file_name = Column(String, nullable=True)
    file_type = Column(String, nullable=True)

    room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User")