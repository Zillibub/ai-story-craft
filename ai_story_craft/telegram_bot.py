from core.settings import settings
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)
import time
import os
from uuid import uuid4
from langfuse.openai import openai
from langfuse.decorators import observe
from collections import deque, defaultdict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from assistant import answer as assistant_answer
from langfuse.decorators import langfuse_context
from db.models_crud import ChatCRUD, AssistantCRUD, ActiveAssistantCRUD, MessageCRUD, now
from session_identifier import TimeoutSessoinIdentifier

# Conversation history dictionary
conversation_history = defaultdict(lambda: deque(maxlen=10))

os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST

openai.api_key = settings.openai_api_key


@observe()
async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    active_assistant = ActiveAssistantCRUD().get_active_assistant(update.message.chat_id)

    if active_assistant is None:
        await update.message.reply_text("No assistant is currently active. Please activate an assistant first.")
        return

    reply = await assistant_answer(
        chat_id=update.message.chat_id,
        session_evaluator=TimeoutSessoinIdentifier(update.message.chat_id, timeout=settings.new_session_timeout),
        prompt=update.message.text, active_assistant_id=active_assistant.assistant.external_id
    )

    await update.message.reply_text(reply)


async def get_assistants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    assistants = AssistantCRUD().get_list()
    reply = "Available assistants:\n" + "\t\n".join([assistant.name for assistant in assistants])
    await update.message.reply_text(reply)


async def get_active_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    active_assistant = ActiveAssistantCRUD().get_active_assistant(update.message.chat_id)

    if active_assistant:
        await update.message.reply_text(f"Active assistant: {active_assistant.assistant.name}")
    else:
        await update.message.reply_text("No active assistant.")


async def activate_assistant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    assistant_name = context.args[0]
    assistant = AssistantCRUD().get_by_name(assistant_name)
    if assistant is None:
        await update.message.reply_text(f"Assistant {assistant_name} not found.")
        return

    active_assistant = ActiveAssistantCRUD().activate_assistant(update.message.chat_id, assistant.id)

    if active_assistant:
        await update.message.reply_text(f"Assistant {assistant_name} activated.")
    else:
        await update.message.reply_text(f"Error activating assistant {assistant_name}.")


@observe()
async def openai_answer(question, assistant_id, thread_id):
    openai.beta.threads.messages.create(
        thread_id=thread_id,
        content=question,
        role="user"
    )
    run = openai.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        # instructions=question
    )
    while run.status == "queued" or run.status == "in_progress":
        run = openai.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id,
        )
        time.sleep(0.2)

    messages = openai.beta.threads.messages.list(
        thread_id=thread_id
    )
    return messages


async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("/assistants", "Get list of available assistants"),
        BotCommand("/activate", "Activate an assistant by name"),
        BotCommand("/active", "Get active assistant name")
    ])


def main():
    application = Application.builder().token(settings.telegram_bot_token).post_init(post_init).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer))
    application.add_handler(CommandHandler("assistants", get_assistants, has_args=False))
    application.add_handler(CommandHandler("activate", activate_assistant, has_args=True))
    application.add_handler(CommandHandler("active", get_active_assistant, has_args=False))
    application.run_polling()


if __name__ == "__main__":
    main()
