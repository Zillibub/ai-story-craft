import openai
import time
from agents import ProductManager
from pathlib import Path
from core.settings import settings
from openai.resources.beta.assistants import Assistant
from langfuse.decorators import langfuse_context
from langfuse.decorators import observe
from session_evaluator import BaseSessionEvaluator
from db.models_crud import ChatCRUD, MessageCRUD


def create_assistant(
        name: str,
        subtitle_file: Path,
) -> Assistant:
    """
    Create an assistant with a file search tool from a given subtitle path file.
    :param name:
    :param subtitle_file:
    :return:
    """
    if not subtitle_file.exists():
        raise FileNotFoundError(f"Subtitle file not found: {subtitle_file}")

    client = openai.Client(api_key=settings.openai_api_key)
    vector_store = client.beta.vector_stores.create(name=subtitle_file.stem)

    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=[open(subtitle_file, "rb")]
    )
    if file_batch.status != "completed":
        raise ValueError(f"File batch upload failed: {file_batch.status}")

    assistant = client.beta.assistants.create(
        model=settings.assistant_model,
        name=name,
        instructions=ProductManager.instructions,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        tools=[{"type": "file_search"}]
    )
    return assistant


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


@observe()
async def answer(
        chat_id,
        session_evaluator: BaseSessionEvaluator,
        prompt,
        active_assistant_id

) -> str:
    chat = ChatCRUD().get_by_external_id(chat_id)
    if chat is None:
        chat = ChatCRUD().create(chat_id=chat_id)

    if chat.openai_thread_id is None:
        openai_thread_id = openai.beta.threads.create().id
        chat = ChatCRUD().update(chat.id, openai_thread_id=openai_thread_id)

        if not chat:
            raise ValueError(f"Chat with id {chat_id} not found")

    session_id = session_evaluator.evaluate()

    langfuse_context.update_current_trace(
        user_id=chat_id,
        session_id=session_id
    )

    messages_history = MessageCRUD().get_session_messages(session_id)
    context = " ".join([message.text for message in messages_history])

    question = context + prompt
    result = await openai_answer(
        question,
        active_assistant_id,
        chat.openai_thread_id
    )
    reply = result.data[0].content[0].text.value
    return reply
