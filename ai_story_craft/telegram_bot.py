from core.settings import settings
from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)
import time
import openai
from collections import deque, defaultdict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models_crud import MessageCRUD, ChatCRUD, AssistantCRUD, ActiveAssistantCRUD
from db.models import Chat

# Conversation history dictionary
conversation_history = defaultdict(lambda: deque(maxlen=10))

engine = create_engine(settings.database_url, echo=True)

Session = sessionmaker(bind=engine)
openai_client = openai.Client(api_key=settings.openai_api_key)

# Chat threads dictionary

chat_threads = {}

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    active_assistant = ActiveAssistantCRUD().get_active_assistant(update.message.chat_id)

    if active_assistant is None:
        await update.message.reply_text("No assistant is currently active. Please activate an assistant first.")
        return

    chat = ChatCRUD().get_by_external_id(update.message.chat_id)
    if chat is None:
        chat = ChatCRUD().create(chat_id=update.message.chat_id)

    if chat.openai_thread_id is None:
        openai_thread_id = openai_client.beta.threads.create().id
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


async def openai_answer(question, assistant_id, thread_id):
    openai_client.beta.threads.messages.create(
        thread_id=thread_id,
        content=question,
        role="user"
    )
    run = openai_client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        # instructions=question
    )
    while run.status == "queued" or run.status == "in_progress":
        run = openai_client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id,
        )
        time.sleep(0.2)

    messages = openai_client.beta.threads.messages.list(
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
