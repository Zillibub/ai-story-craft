from core.settings import settings
from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    filters,
)
import time
import openai
from collections import deque, defaultdict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models_crud import MessageCRUD, ChatCRUD

# Conversation history dictionary
conversation_history = defaultdict(lambda: deque(maxlen=10))

engine = create_engine(settings.database_url, echo=True)

Session = sessionmaker(bind=engine)
openai_client = openai.Client(api_key=settings.openai_api_key)

# Chat threads dictionary

chat_threads = {}


def log_question_and_answer(external_chat_id, question, answer):
    session = Session()
    chat = ChatCRUD().get_by_external_id(external_chat_id)
    if not chat:
        raise ValueError(f"Chat with id {external_chat_id} not found")
    chat_log = MessageCRUD().create(chat_id=chat.id, question=question, answer=answer)


async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat_id not in chat_threads.keys():
        chat_threads[update.message.chat_id] = openai_client.beta.threads.create().id

    question = update.message.text

    result = await openai_answer(question, settings.assistant_id, chat_threads[update.message.chat_id])
    reply = result.data[0].content[0].text.value
    log_question_and_answer(update.message.chat_id, question, reply)
    await update.message.reply_text(reply)


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

    application.run_polling()


if __name__ == "__main__":
    main()