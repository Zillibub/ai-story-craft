from core.settings import settings
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)
from typing import Union
from pathlib import Path
import openai
# from langfuse.openai import openai
# from langfuse.decorators import observe
from collections import deque, defaultdict
from db.models_crud import AgentCRUD, ActiveAgentCRUD, ChatCRUD
from rag.agent_manager import AgentManager
from rag.langchain_agent import LangChanAgent

# Conversation history dictionary
conversation_history = defaultdict(lambda: deque(maxlen=10))

# os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
# os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
# os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST

openai.api_key = settings.OPENAI_API_KEY

async def retrieve_active_agent(update: Update) ->Union[None, LangChanAgent]:
    chat = ChatCRUD().get_by_external_id(str(update.message.chat_id))
    active_agent = ActiveAgentCRUD().get_active_agent(chat.id)

    if active_agent is None:
        await update.message.reply_text("No video is currently selected. Please select a video first.")
        return

    agent = AgentManager().get(active_agent.agent_id)
    return agent


# @observe()
async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agent = await retrieve_active_agent(update)

    if agent is None:
        return

    question = update.message.text

    reply = agent.answer(question, conversation_history[update.message.chat_id])

    conversation_history[update.message.chat_id].append({'question': question, 'answer': reply})

    await update.message.reply_text(reply)


async def get_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agent = await retrieve_active_agent(update)
    if agent is None:
        return

    description = context.args[0]
    if not description:
        await update.message.reply_text("Please provide Screenshot description")
        return

    image_bytes, image_name = agent.get_image(update.message.text)
    await update.message.reply_document(
        document=image_bytes,
        write_timeout=500,
        filename=image_name,
        reply_to_message_id=update.message.id
    )


async def get_agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agents = AgentCRUD().get_list()
    if len(agents) == 0:
        reply = "No videos available."
    else:
        reply = "Available videos:\n" + "\t\n".join([agent.name for agent in agents])
    await update.message.reply_text(reply)


async def get_active_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = ChatCRUD().get_by_external_id(str(update.message.chat_id))
    active_agent = ActiveAgentCRUD().get_active_agent(chat.id)

    if active_agent:
        await update.message.reply_text(
            f"Active video: {active_agent.agent.name} \n\n "
            f"Description: {active_agent.agent.description} \n"
            f"Id: {active_agent.agent.id}"
        )
    else:
        await update.message.reply_text("No active video.")


async def activate_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agent_name = context.args[0]
    if not agent_name:
        await update.message.reply_text("Please provide an video name.")
        return

    agent = AgentCRUD().get_by_name(agent_name)
    if agent is None:
        await update.message.reply_text(f"Video {agent_name} not found.")
        return

    chat = ChatCRUD().get_by_external_id(str(update.message.chat_id))
    if chat is None:
        chat = ChatCRUD().create(chat_id=update.message.chat_id)

    active_agent = ActiveAgentCRUD().activate_agent(chat.id, agent.id)

    if active_agent:
        await update.message.reply_text(f"Video {agent_name} Selected.")
    else:
        await update.message.reply_text(f"Error activating video {agent_name}.")

async def create_story_map(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agent = await retrieve_active_agent(update)
    if agent is None:
        return

    story_map = agent.create_user_story_map()
    story_map = agent.apply_telegram_formating(story_map)
    await update.message.reply_text(story_map)



async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("/videos", "Get list of available Videos"),
        BotCommand("/select", "Select a video for analysis"),
        BotCommand("/selected", "Get selected for analysis video"),
        BotCommand("/screenshot", "Get screenshot of the video"),
        BotCommand("/story_map", "Create a user story map for selected video")

    ])
    load_agents()

def load_agents():
    agents = AgentCRUD().get_list()
    for agent in agents:
        AgentManager().add(agent.id, LangChanAgent.load(Path(agent.agent_dir)))



def main():
    application = Application.builder().token(settings.telegram_bot_token).post_init(post_init).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer))
    application.add_handler(CommandHandler("videos", get_agents, has_args=False))
    application.add_handler(CommandHandler("select", activate_agent, has_args=True))
    application.add_handler(CommandHandler("selected", get_active_agent, has_args=False))
    application.add_handler(CommandHandler("screenshot", get_screenshot, has_args=True))
    application.add_handler(CommandHandler("story_map", create_story_map, has_args=False))
    application.run_polling()


if __name__ == "__main__":
    main()
