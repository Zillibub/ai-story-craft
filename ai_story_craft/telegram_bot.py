from core.settings import settings
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)
import os
from langfuse.openai import openai
from langfuse.decorators import observe
from collections import deque, defaultdict
from db.models_crud import AgentCRUD, ActiveAgentCRUD, ChatCRUD
from rag.agent_manager import AgentManager

# Conversation history dictionary
conversation_history = defaultdict(lambda: deque(maxlen=10))

os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST

openai.api_key = settings.OPENAI_API_KEY


@observe()
async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    active_agent = ActiveAgentCRUD().get_active_agent(update.message.chat_id)

    if active_agent is None:
        await update.message.reply_text("No agent is currently active. Please activate an agent first.")
        return

    agent = AgentManager().get(active_agent.agent_id)

    reply = agent.answer(update.message.text)

    await update.message.reply_text(reply)


async def get_agents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agents = AgentCRUD().get_list()
    if len(agents) == 0:
        reply = "No agents available."
    else:
        reply = "Available agents:\n" + "\t\n".join([agent.name for agent in agents])
    await update.message.reply_text(reply)


async def get_active_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = ChatCRUD().get_by_external_id(str(update.message.chat_id))
    active_agent = ActiveAgentCRUD().get_active_agent(chat.id)

    if active_agent:
        await update.message.reply_text(
            f"Active agent: {active_agent.agent.name} \n\n "
            f"Description: {active_agent.agent.description} \n"
            f"Id: {active_agent.agent.external_id}"
        )
    else:
        await update.message.reply_text("No active agent.")


async def activate_agent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agent_name = context.args[0]
    agent = AgentCRUD().get_by_name(agent_name)
    if agent is None:
        await update.message.reply_text(f"agent {agent_name} not found.")
        return

    chat = ChatCRUD().get_by_external_id(str(update.message.chat_id))
    if chat is None:
        chat = ChatCRUD().create(chat_id=update.message.chat_id)

    active_agent = ActiveAgentCRUD().activate_agent(chat.id, agent.id)

    if active_agent:
        await update.message.reply_text(f"agent {agent_name} activated.")
    else:
        await update.message.reply_text(f"Error activating agent {agent_name}.")


async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("/agents", "Get list of available agents"),
        BotCommand("/activate", "Activate an agent by name"),
        BotCommand("/active", "Get active agent name")
    ])
    load_agents()

def load_agents():
    agents = AgentCRUD().get_list()
    for agent in agents:
        AgentManager().add(agent.id, agent)



def main():
    application = Application.builder().token(settings.telegram_bot_token).post_init(post_init).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer))
    application.add_handler(CommandHandler("agents", get_agents, has_args=False))
    application.add_handler(CommandHandler("activate", activate_agent, has_args=True))
    application.add_handler(CommandHandler("active", get_active_agent, has_args=False))
    application.run_polling()


if __name__ == "__main__":
    main()
