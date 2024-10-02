from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String, nullable=False)
    openai_thread_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())
    chat_type = Column(Enum('telegram', name='chat_types'), default='telegram')


class Agent(Base):
    __tablename__ = 'agents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=func.now())
    description = Column(String, nullable=True)


class ActiveAssistant(Base):
    __tablename__ = 'active_agents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    agents_id = Column(Integer, ForeignKey('agents.id'))
    activated_at = Column(DateTime, default=func.now())

    chat = relationship('Chat')
    agent = relationship('Agent')


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    agent_id = Column(Integer, ForeignKey('agents.id'))

    session_id = Column(String, nullable=False)
    message = Column(String, nullable=False)
    direction = Column(String)
    created_at = Column(DateTime, default=func.now())

    chat = relationship('Chat')
    agent = relationship('Agent')
