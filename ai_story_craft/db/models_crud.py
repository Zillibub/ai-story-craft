from db.base_crud import CRUD, engine
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from db.models import Chat, Agent, ActiveAgent, Message


def now():
    return func.current_timestamp(bind=engine)


class ChatCRUD(CRUD):
    def __init__(self):
        super().__init__(Chat)

    def get_by_external_id(self, chat_id):
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(chat_id=chat_id).first()
        return instance


class AgentCRUD(CRUD):
    def __init__(self):
        super().__init__(Agent)

    def get_list(self, page_number: int = 0, page_size: int = 10):
        with self.scoped_session() as session:
            instances = session.query(self.model).limit(page_size).offset(page_size * page_number).all()
        return instances

    def get_by_name(self, name: str):
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(name=name).first()
        return instance


class ActiveAgentCRUD(CRUD):
    def __init__(self):
        super().__init__(ActiveAgent)

    def activate_agent(self, chat_id: int, assistant_id: int):
        with self.scoped_session().begin():
            instance = self.scoped_session.query(self.model).filter_by(chat_id=chat_id).first()
            if instance is None:
                instance = self.model(chat_id=chat_id, assistant_id=assistant_id)
            else:
                instance.assistant_id = assistant_id
            self.scoped_session.add(instance)
        return instance

    def get_by_chat_id(self, chat_id: int):
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(chat_id=chat_id).first()
        return instance

    def get_active_agent(self, chat_id: int):
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(chat_id=chat_id).options(
                selectinload(self.model.assistant)).first()
        return instance


class MessageCRUD(CRUD):
    def __init__(self):
        super().__init__(Message)

    def get_last_interaction(self, chat_id: int):
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(chat_id=chat_id).order_by(self.model.id.desc()).first()
        return instance

    def get_last_session(self, chat_id: int):
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(chat_id=chat_id).order_by(self.model.id.desc()).first()
        return instance

    def get_session_messages(self, session_id: int):
        with self.scoped_session() as session:
            instances = session.query(self.model).filter_by(session_id=session_id).all()
        return instances
