from core.settings import settings
import discord
from discord import Message, Client, app_commands
from typing import Union
import openai
import io
from collections import deque, defaultdict
from db.models_crud import AgentCRUD, ActiveAgentCRUD, ChatCRUD
from agent_manager import AgentManager
from rag.langchain_agent import LangChanAgent
from celery_app import process_youtube_video, check_celery_worker
from video_processing.youtube_video_processor import YoutubeVideoProcessor
from integrations.discord_messenger import DiscordMessageSender

intents = discord.Intents.default()
intents.message_content = True

# bot = commands.Bot(command_prefix='$', intents=intents)

# Conversation history dictionary
conversation_history = defaultdict(lambda: deque(maxlen=10))
openai.api_key = settings.OPENAI_API_KEY

client = Client(intents=intents)
tree = app_commands.CommandTree(client)


def update_conversation_history(channel_id, question, answer):
    conversation_history[channel_id].append({'question': question, 'answer': answer})


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
    update_conversation_history(message.channel.id, question, reply)

    await message.channel.send(reply)


async def retrieve_active_agent(interaction: Union[discord.Interaction, discord.Message]) -> Union[None, LangChanAgent]:
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


@tree.command(name='screenshot', description='Get screenshot')
async def screenshot(interaction: discord.Interaction, description: str):
    await interaction.response.defer()  # noqa no idea why pycharm complains about this, it works

    agent = await retrieve_active_agent(interaction)
    if agent is None:
        return
    if not description:
        await interaction.followup.send("Please provide Screenshot description")
        return

    image_bytes, image_name, readable_timestamp = agent.get_image(description)
    await interaction.followup.send(
        f"Timestamp: {readable_timestamp}",
        file=discord.File(io.BytesIO(image_bytes), filename=image_name)
    )


@tree.command(name='videos', description='List available videos')
async def get_agents(interaction: discord.Interaction):
    await interaction.response.defer()  # noqa
    agents = AgentCRUD().get_list()
    if len(agents) == 0:
        reply = "No videos available."
    else:
        reply = "Available videos:\n" + "\t\n".join([agent.name for agent in agents])
    await interaction.followup.send(reply)


@tree.command(name='selected', description='Get selected video')
async def get_active_agent(interaction: discord.Interaction):
    await interaction.response.defer()  # noqa
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


@tree.command(name='select', description='Select video for analysis')
async def activate_agent(interaction: discord.Interaction, agent_name: str):
    await interaction.response.defer()  # noqa
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


@tree.command(name='story_map', description='Generate story map for selected video')
async def story_map(interaction: discord.Interaction):
    await interaction.response.defer()  # noqa

    agent = await retrieve_active_agent(interaction)
    if agent is None:
        return

    story_map = agent.create_user_story_map()
    update_conversation_history(interaction.channel_id, "User story map", story_map)
    story_map_chunks = agent.apply_discord_formating(story_map)
    for chunk in story_map_chunks:
        await interaction.followup.send(chunk)


@tree.command(name='add_video', description='Add video for analysis')
async def add_video(interaction: discord.Interaction, video_url: str):
    await interaction.response.defer()  # noqa

    is_worker_running = check_celery_worker()
    if not is_worker_running:
        await interaction.followup.send("Video import is not available. Please try again later.")
        return

    try:
        YoutubeVideoProcessor.check_availability(video_url)
    except ValueError as e:
        await interaction.followup.send(f"Error processing video: {str(e)}")
        return

    if YoutubeVideoProcessor.get_duration(video_url) > settings.max_video_duration:
        await interaction.followup.send(
            f"Video is too long. Maximum duration is {settings.max_video_duration} seconds."
        )
        return

    message = await interaction.followup.send(f"Starting video processing")
    process_youtube_video.delay(
        youtube_url=video_url,
        update_sender=DiscordMessageSender(interaction.channel_id, message.id).to_dict()
    )


@tree.command(name='help', description='Get help')
async def help_command(interaction: discord.Interaction):
    await interaction.response.defer()  # noqa
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
