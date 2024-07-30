from db.base_crud import CRUD
from db.models import Chat, Assistant, ActiveAssistant, Message


class ChatCRUD(CRUD):
    def __init__(self):
        super().__init__(Chat)

    def get_by_external_id(self, chat_id):
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(chat_id=chat_id).first()
        return instance


class AssistantCRUD(CRUD):
    def __init__(self):
        super().__init__(Assistant)

    def get_list(self, page_number: int = 0, page_size: int = 10):
        with self.scoped_session() as session:
            instances = session.query(self.model).limit(page_size).offset(page_size * (page_number - 1)).all()
        return instances


class ActiveAssistantCRUD(CRUD):
    def __init__(self):
        super().__init__(ActiveAssistant)

    def get_active_assistant(self, chat_id: int):
        with self.scoped_session() as session:
            instance = session.query(self.model).filter_by(chat_id=chat_id).first()
        return instance


class MessageCRUD(CRUD):
    def __init__(self):
        super().__init__(Message)
