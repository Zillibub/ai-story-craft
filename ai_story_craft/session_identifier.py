from uuid import uuid4
from abc import ABC, abstractmethod
from db.models_crud import MessageCRUD, now


class BaseSessionIdentifier(ABC):

    @abstractmethod
    def identify(self):
        raise NotImplementedError()


class FixedSessionIdentifier(BaseSessionIdentifier):
    def __init__(self, session_id):
        self.session_id = session_id

    def identify(self):
        return self.session_id


class TimeoutSessoinIdentifier(BaseSessionIdentifier):
    """
    Creates new sessoin id if time elapsed from the last message is bigger than given timeout
    """

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
