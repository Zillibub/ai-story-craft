from core.settings import settings
from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)
import logging
import time
import os
from langfuse.openai import openai
from langfuse.decorators import observe
from collections import deque, defaultdict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from langfuse.decorators import langfuse_context
from db.models_crud import MessageCRUD, ChatCRUD, AssistantCRUD, ActiveAssistantCRUD

# Conversation history dictionary
conversation_history = defaultdict(lambda: deque(maxlen=10))

engine = create_engine(settings.database_url, echo=True)

Session = sessionmaker(bind=engine)

os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LANGFUSE_PUBLIC_KEY
os.environ["LANGFUSE_SECRET_KEY"] = settings.LANGFUSE_SECRET_KEY
os.environ["LANGFUSE_HOST"] = settings.LANGFUSE_HOST

openai.langfuse_public_key = settings.LANGFUSE_PUBLIC_KEY
openai.langfuse_secret_key = settings.LANGFUSE_SECRET_KEY
openai.langfuse_enabled = True
openai.langfuse_host = settings.LANGFUSE_HOST
openai.api_key = settings.openai_api_key

langfuse_context._get_langfuse().log.setLevel(logging.DEBUG)

@observe()
async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    active_assistant = ActiveAssistantCRUD().get_active_assistant(update.message.chat_id)

    if active_assistant is None:
        await update.message.reply_text("No assistant is currently active. Please activate an assistant first.")
        return

    chat = ChatCRUD().get_by_external_id(update.message.chat_id)
    if chat is None:
        chat = ChatCRUD().create(chat_id=update.message.chat_id)

    if chat.openai_thread_id is None:
        openai_thread_id = openai.beta.threads.create().id
        chat = ChatCRUD().update(chat.id, openai_thread_id=openai_thread_id)

        if not chat:
            raise ValueError(f"Chat with id {update.message.chat_id} not found")

    question = update.message.text

    MessageCRUD().create(
        chat_id=chat.id,
        assistant_id=active_assistant.assistant_id,
        message=question,
        direction='incoming'
    )

    result = await openai_answer(
        question,
        active_assistant.assistant.external_id,
        chat.openai_thread_id
    )

    reply = result.data[0].content[0].text.value

    MessageCRUD().create(
        chat_id=chat.id,
        assistant_id=active_assistant.assistant_id,
        message=reply,
        direction='outgoing'
    )

    langfuse_client = langfuse_context._get_langfuse()
    # pass trace_id and current observation ids to the newly created child generation
    langfuse_client.generation(
        trace_id=langfuse_context.get_current_trace_id(),
        parent_observation_id=langfuse_context.get_current_observation_id(),
        input=question,
        output=result
    )

    langfuse_context.flush()

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


def main():
    application = Application.builder().token(settings.telegram_bot_token).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.Regex("^Ingest"), answer))
    application.add_handler(CommandHandler("assistants", get_assistants, has_args=False))
    application.add_handler(CommandHandler("activate", activate_assistant, has_args=True))
    application.add_handler(CommandHandler("active", get_active_assistant, has_args=False))
    application.run_polling()


if __name__ == "__main__":
    main()
