import telegram
from core.settings import settings

class MessageSender:

    def __init__(self, chat_id: int, update_message_id: int):
        self.chat_id = chat_id
        self.update_message_id = update_message_id

    async def send_message(self, text: str):
        await telegram.Bot(settings.telegram_bot_token).sendMessage(chat_id=self.chat_id, text=text)

    async def update_message(self, text: str):
        """
        Update message
        :param text:
        :return:
        :raises ValueError: if no update_message_id given
        """
        if not self.update_message_id:
            raise ValueError("no update_message_id given")

        await telegram.Bot(settings.telegram_bot_token).editMessageText(
            chat_id=self.chat_id, message_id=self.update_message_id, text=text)
