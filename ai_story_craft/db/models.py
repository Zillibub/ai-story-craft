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


class Assistant(Base):
    __tablename__ = 'assistants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
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
    chat_id = Column(Integer, ForeignKey('chats.id'))
    assistant_id = Column(Integer, ForeignKey('assistants.id'))
    message = Column(String, nullable=False)
    direction = Column(String, CheckConstraint("direction IN ('incoming', 'outgoing')"))
    created_at = Column(DateTime, default=func.now())

    chat = relationship('Chat')
    assistant = relationship('Assistant')
