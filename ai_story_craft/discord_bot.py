
from core.settings import settings
import discord
from discord import Message
from typing import Union
import openai
from collections import deque, defaultdict
from db.models_crud import AgentCRUD, ActiveAgentCRUD, ChatCRUD
from agent_manager import AgentManager
from rag.langchain_agent import LangChanAgent
from celery_app import process_youtube_video
from integrations.telegram import MessageSender
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

# Conversation history dictionary
conversation_history = defaultdict(lambda: deque(maxlen=10))
openai.api_key = settings.OPENAI_API_KEY

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message: Message):
    if message.author == bot.user:
        return

    agent = await retrieve_active_agent(message)

    if agent is None:
        return

    question = message.content

    reply = agent.answer(question, conversation_history[message.channel.id])

    conversation_history[message.channel.id].append({'question': question, 'answer': reply})

    await message.channel.send(reply)


async def retrieve_active_agent(message: Message) -> Union[None, LangChanAgent]:
    chat = ChatCRUD().get_by_external_id(str(message.channel.id))
    if chat is None:
        await message.channel.send("No video is currently selected. Please select a video first.")
        return

    active_agent = ActiveAgentCRUD().get_active_agent(chat.id)

    if active_agent is None:
        await message.channel.send("No video is currently selected. Please select a video first.")
        return

    agent = AgentManager().get(active_agent.agent_id)
    return agent

@bot.command(name='screenshot')
async def get_screenshot(message: Message, description: str):
    agent = await retrieve_active_agent(message)
    if agent is None:
        return
    if not description:
        await message.channel.send("Please provide Screenshot description")
        return

    image_bytes, image_name = agent.get_image(description)
    await message.channel.send(file=discord.File(image_bytes, filename=image_name))


@bot.command(name='videos')
async def get_agents(message: Message):
    agents = AgentCRUD().get_list()
    if len(agents) == 0:
        reply = "No videos available."
    else:
        reply = "Available videos:\n" + "\t\n".join([agent.name for agent in agents])
    await message.channel.send(reply)


@bot.command(name='selected')
async def get_active_agent(message: Message):
    chat = ChatCRUD().get_by_external_id(str(message.channel.id))
    active_agent = ActiveAgentCRUD().get_active_agent(chat.id)

    if active_agent:
        await message.channel.send(
            f"Active video: {active_agent.agent.name} \n\n "
            f"Description: {active_agent.agent.description} \n"
            f"Id: {active_agent.agent.id}"
        )
    else:
        await message.channel.send("No active video.")


@bot.command(name='select')
async def activate_agent(message: Message, agent_name: str):
    if not agent_name:
        await message.channel.send("Please provide an video name.")
        return

    agent = AgentCRUD().get_by_name(agent_name)
    if agent is None:
        await message.channel.send(f"Video {agent_name} not found.")
        return

    chat = ChatCRUD().get_by_external_id(str(message.channel.id))
    if chat is None:
        chat = ChatCRUD().create(chat_id=message.channel.id)

    active_agent = ActiveAgentCRUD().activate_agent(chat.id, agent.id)

    if active_agent:
        await message.channel.send(f"Video {agent_name} Selected.")
    else:
        await message.channel.send(f"Error activating video {agent_name}.")


@bot.command(name='story_map')
async def create_story_map(message: Message):
    agent = await retrieve_active_agent(message)
    if agent is None:
        return

    story_map = agent.create_user_story_map()
    story_map = agent.apply_telegram_formating(story_map)[:4096]
    await message.channel.send(story_map)


@bot.command(name='add_video')
async def add_video(message: Message, video_url: str):
    message = await message.channel.send(f"Starting video processing")
    process_youtube_video.delay(
        youtube_url=video_url,
        update_sender=MessageSender(message.channel.id, message.id).to_dict()
    )


def main():
    bot.run(settings.discord_bot_token)


if __name__ == "__main__":
    main()
