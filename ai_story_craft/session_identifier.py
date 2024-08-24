from uuid import uuid4
from abc import ABC, abstractmethod
from db.models_crud import MessageCRUD, now

class BaseSessionIdentifier(ABC):

    @abstractmethod
    def identify(self):
        raise NotImplementedError()


class TimeoutSessoinIdentifier(BaseSessionIdentifier):

    def __init__(
            self,
            chat_id: int,
            timeout: int
    ):
        self.chat_id = chat_id
        self.timeout = timeout

    def identify(self):
        if now() - MessageCRUD().get_last_interaction(self.chat_id) > self.timeout:
            session_id = uuid4()
        else:
            session_id = MessageCRUD().get_last_session(self.chat_id).id
        return session_id