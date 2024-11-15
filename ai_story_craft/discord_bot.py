from core.settings import settings
import discord
from discord import Message, Client, app_commands
from typing import Union
import openai
from collections import deque, defaultdict
from db.models_crud import AgentCRUD, ActiveAgentCRUD, ChatCRUD
from agent_manager import AgentManager
from rag.langchain_agent import LangChanAgent
from celery_app import process_youtube_video
from integrations.telegram import MessageSender

intents = discord.Intents.default()
intents.message_content = True

# bot = commands.Bot(command_prefix='$', intents=intents)

# Conversation history dictionary
conversation_history = defaultdict(lambda: deque(maxlen=10))
openai.api_key = settings.OPENAI_API_KEY

client = Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    await tree.sync()
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message: Message):
    if message.author == client.user:
        return

    agent = await retrieve_active_agent(message)

    if agent is None:
        return

    question = message.content

    reply = agent.answer(question, conversation_history[message.channel.id])

    conversation_history[message.channel.id].append({'question': question, 'answer': reply})

    await message.channel.send(reply)


async def retrieve_active_agent(interaction: discord.Interaction) -> Union[None, LangChanAgent]:
    await interaction.response.defer()

    chat = ChatCRUD().get_by_external_id(str(interaction.channel.id))
    if chat is None:
        await interaction.followup.send("No video is currently selected. Please select a video first.")
        return

    active_agent = ActiveAgentCRUD().get_active_agent(chat.id)

    if active_agent is None:
        await interaction.followup.send("No video is currently selected. Please select a video first.")
        return

    agent = AgentManager().get(active_agent.agent_id)
    return agent


@tree.command(name='screenshot')
async def get_screenshot(interaction: discord.Interaction, description: str):
    await interaction.response.defer()
    agent = await retrieve_active_agent(interaction.message)
    if agent is None:
        return
    if not description:
        await interaction.followup.send("Please provide Screenshot description")
        return

    image_bytes, image_name = agent.get_image(description)
    await interaction.followup.send(file=discord.File(image_bytes, filename=image_name))


@tree.command(name='videos')
async def get_agents(interaction: discord.Interaction):
    await interaction.response.defer()
    agents = AgentCRUD().get_list()
    if len(agents) == 0:
        reply = "No videos available."
    else:
        reply = "Available videos:\n" + "\t\n".join([agent.name for agent in agents])
    await interaction.followup.send(reply)


@tree.command(name='selected')
async def get_active_agent(interaction: discord.Interaction):
    await interaction.response.defer()
    chat = ChatCRUD().get_by_external_id(str(interaction.channel.id))
    active_agent = ActiveAgentCRUD().get_active_agent(chat.id)

    if active_agent:
        await interaction.followup.send(
            f"Active video: {active_agent.agent.name} \n\n "
            f"Description: {active_agent.agent.description} \n"
            f"Id: {active_agent.agent.id}"
        )
    else:
        await interaction.followup.send("No active video.")


@tree.command(name='select')
async def activate_agent(interaction: discord.Interaction, agent_name: str):
    await interaction.response.defer()
    if not agent_name:
        await interaction.followup.send("Please provide an video name.")
        return

    agent = AgentCRUD().get_by_name(agent_name)
    if agent is None:
        await interaction.followup.send(f"Video {agent_name} not found.")
        return

    chat = ChatCRUD().get_by_external_id(str(interaction.channel.id))
    if chat is None:
        chat = ChatCRUD().create(chat_id=interaction.channel.id)

    active_agent = ActiveAgentCRUD().activate_agent(chat.id, agent.id)

    if active_agent:
        await interaction.followup.send(f"Video {agent_name} Selected.")
    else:
        await interaction.followup.send(f"Error activating video {agent_name}.")


@tree.command(name='story_map')
async def create_story_map(interaction: discord.Interaction):
    await interaction.response.defer()

    agent = await retrieve_active_agent(interaction.message)
    if agent is None:
        return

    story_map = agent.create_user_story_map()
    story_map = agent.apply_telegram_formating(story_map)[:4096]
    await interaction.followup.send(story_map)


@tree.command(name='add_video')
async def add_video(interaction: discord.Interaction, video_url: str):
    await interaction.response.defer()
    message = await interaction.followup.send(f"Starting video processing")
    process_youtube_video.delay(
        youtube_url=video_url,
        update_sender=MessageSender(message.channel.id, message.id).to_dict()
    )


@tree.command(name='help', description='Get help')
async def help_command(interaction: discord.Interaction):
    await interaction.response.defer()
    await interaction.followup.send(
        "Available commands:\n"
        "/videos - List available videos\n"
        "/selected - Get selected video\n"
        "/select <video_name> - Select video\n"
        "/story_map - Generate story map\n"
        "/add_video <youtube_url> - Add video\n"
        "/screenshot <description> - Get screenshot\n"
        "/help - Get help"
    )


def main():
    client.run(settings.discord_bot_token)


if __name__ == "__main__":
    main()
