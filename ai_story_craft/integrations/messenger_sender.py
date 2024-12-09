import telegram
import asyncio
import discord
from core.settings import settings


class BaseMessageSender:
    def send_message(self, text: str):
        raise NotImplementedError

    def update_message(self, text: str):
        raise NotImplementedError

    def to_dict(self):
        raise NotImplementedError

    @property
    def external_chat_id(self) -> str:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data):
        raise NotImplementedError


class TelegramMessageSender(BaseMessageSender):

    def __init__(self, chat_id: int, update_message_id: int):
        self.chat_id = chat_id
        self.update_message_id = update_message_id

    @property
    def external_chat_id(self) -> str:
        return str(self.chat_id)

    def send_message(self, text: str):
        asyncio.run(telegram.Bot(settings.telegram_bot_token).sendMessage(chat_id=self.chat_id, text=text))

    def update_message(self, text: str):
        """
        Update message
        :param text:
        :return:
        :raises ValueError: if no update_message_id given
        """
        if not self.update_message_id:
            raise ValueError("no update_message_id given")

        asyncio.run(telegram.Bot(settings.telegram_bot_token).editMessageText(
            chat_id=self.chat_id, message_id=self.update_message_id, text=text))

    def to_dict(self):
        return {
            'class': self.__class__.__name__,
            'chat_id': self.chat_id,
            'update_message_id': self.update_message_id
        }

    @classmethod
    def from_dict(cls, data):
        return cls(chat_id=data['chat_id'], update_message_id=data['update_message_id'])


class DiscordMessageSender(BaseMessageSender):
    def __init__(self, channel_id: int, update_message_id: int):
        self.channel_id = channel_id
        self.update_message_id = update_message_id
        self.client = None

    async def _get_client(self):
        if self.client is None or self.client.is_closed():
            self.client = discord.Client(intents=discord.Intents.default())
            await self.client.login(settings.discord_bot_token)
        return self.client

    async def _get_channel(self):
        client = await self._get_client()
        return await client.fetch_channel(self.channel_id)

    async def _get_message(self):
        channel = await self._get_channel()
        return await channel.fetch_message(self.update_message_id)

    async def _send_message(self, text: str):
        channel = await self._get_channel()
        await channel.send(text)

    @property
    def external_chat_id(self) -> str:
        return str(self.channel_id)

    def send_message(self, text: str):
        asyncio.run(self._send_message(text))

    async def _update_message(self, text: str):
        if not self.update_message_id:
            raise ValueError("no update_message_id given")

        message = await self._get_message()
        await message.edit(content=text)

    def update_message(self, text: str):
        asyncio.run(self._update_message(text))

    def to_dict(self):
        return {
            'class': self.__class__.__name__,
            'channel_id': self.channel_id,
            'update_message_id': self.update_message_id
        }

    @classmethod
    def from_dict(cls, data):
        return cls(channel_id=data['channel_id'], update_message_id=data['update_message_id'])


def messenger_factory(messenger_dict) -> BaseMessageSender:
    if messenger_dict['class'] == TelegramMessageSender.__name__:
        return TelegramMessageSender.from_dict(messenger_dict)
    elif messenger_dict['class'] == DiscordMessageSender.__name__:
        return DiscordMessageSender.from_dict(messenger_dict)
    else:
        raise ValueError("Invalid class name in messenger_dict")
