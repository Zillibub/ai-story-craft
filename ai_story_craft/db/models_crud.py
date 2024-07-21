from db.base_crud import CRUD
from db.models import User, Assistant, ActiveAssistant, Message


class UserCRUD(CRUD):
    def __init__(self):
        super().__init__(User)


class AssistantCRUD(CRUD):
    def __init__(self):
        super().__init__(Assistant)


class ActiveAssistantCRUD(CRUD):
    def __init__(self):
        super().__init__(ActiveAssistant)


class MessageCRUD(CRUD):
    def __init__(self):
        super().__init__(Message)
