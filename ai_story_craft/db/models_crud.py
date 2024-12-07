from db.base_crud import CRUD, engine
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from db.models import Chat, Agent, ActiveAgent, Message, Video, AgentAccess


def now():
    return func.current_timestamp(bind=engine)


class ChatCRUD(CRUD):
    def __init__(self):
        super().__init__(Chat)

    def get_by_external_id(self, chat_id) -> Chat | None:
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(chat_id=chat_id).first()
        return instance

class VideoCRUD(CRUD):
    def __init__(self):
        super().__init__(Video)

    def get_by_hash(self, hash_sum: str) -> Video | None:
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(hash_sum=hash_sum).first()
        return instance


class AgentCRUD(CRUD):
    def __init__(self):
        super().__init__(Agent)

    def get_list(self, page_number: int = 0, page_size: int = 10) -> list[Agent]:
        with self.scoped_session() as session:
            instances = session.query(self.model).limit(page_size).offset(page_size * page_number).all()
        return instances

    def get_by_name(self, name: str) -> Agent | None:
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(name=name).first()
        return instance


class ActiveAgentCRUD(CRUD):
    def __init__(self):
        super().__init__(ActiveAgent)

    def activate_agent(self, chat_id: int, agent_id: int) -> ActiveAgent:
        with self.scoped_session().begin():
            instance = self.scoped_session.query(self.model).filter_by(chat_id=chat_id).first()
            if instance is None:
                instance = self.model(chat_id=chat_id, agent_id=agent_id)
            else:
                instance.agent_id = agent_id
            self.scoped_session.add(instance)
        return instance

    def get_by_chat_id(self, chat_id: int) -> ActiveAgent | None:
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(chat_id=chat_id).first()
        return instance

    def get_active_agent(self, chat_id: int) -> ActiveAgent | None:
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(chat_id=chat_id).options(
                selectinload(self.model.agent)).first()
        return instance

    def get_by_agent_id(self, agent_id: int) -> list[ActiveAgent]:
        with self.scoped_session() as session:
            instances = session.query(self.model).filter_by(agent_id=agent_id).all()
        return instances


class MessageCRUD(CRUD):
    def __init__(self):
        super().__init__(Message)

    def get_last_interaction(self, chat_id: int) -> Message | None:
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(chat_id=chat_id).order_by(self.model.id.desc()).first()
        return instance

    def get_last_session(self, chat_id: int) -> Message | None:
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(chat_id=chat_id).order_by(self.model.id.desc()).first()
        return instance

    def get_session_messages(self, session_id: int) -> list[Message]:
        with self.scoped_session() as session:
            instances = session.query(self.model).filter_by(session_id=session_id).all()
        return instances


class AgentAccessCRUD(CRUD):
    def __init__(self):
        super().__init__(AgentAccess)

    def get_by_chat_and_agent(self, chat_id: int, agent_id: int) -> AgentAccess | None:
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(
                chat_id=chat_id, 
                agent_id=agent_id
            ).first()
        return instance

    def get_chat_agents(self, chat_id: int) -> list[AgentAccess]:
        with self.scoped_session() as session:
            instances = session.query(self.model).filter_by(chat_id=chat_id).all()
        return instances

    def grant_access(self, chat_id: int, agent_id: int) -> AgentAccess:
        with self.scoped_session() as session:
            instance = self.model(chat_id=chat_id, agent_id=agent_id)
            session.add(instance)
            session.commit()
        return instance
