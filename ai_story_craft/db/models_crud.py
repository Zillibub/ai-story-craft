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


class ActiveAssistantCRUD(CRUD):
    def __init__(self):
        super().__init__(ActiveAssistant)


class MessageCRUD(CRUD):
    def __init__(self):
        super().__init__(Message)
