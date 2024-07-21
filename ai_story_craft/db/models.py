from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())


class Assistant(Base):
    __tablename__ = 'assistants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    model = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())


class ActiveAssistant(Base):
    __tablename__ = 'active_assistants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    assistant_id = Column(Integer, ForeignKey('assistants.id'))
    activated_at = Column(DateTime, default=func.now())

    user = relationship('User')
    assistant = relationship('Assistant')


class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    assistant_id = Column(Integer, ForeignKey('assistants.id'))
    message = Column(String, nullable=False)
    direction = Column(String, CheckConstraint("direction IN ('incoming', 'outgoing')"))
    created_at = Column(DateTime, default=func.now())

    user = relationship('User')
    assistant = relationship('Assistant')
