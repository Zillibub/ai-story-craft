import openai
from pathlib import Path
from core.settings import settings
from openai.resources.beta.assistants import Assistant


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
        instructions="""You are a senior product manager who analyses the product videos.
        You will be provided with a video subtitles. Use only the provided information to answer the user's questions.
        Use the following formatting in our answers: 
        <b>text</b> - Bold text, <i>text</i> - Italicize text, <u>text</u> - Underline text, 
        <s>text</s> - Strikethrough text, <code>text</code> - highlight part of a piece of code
        <tg-spoiler>text</tg-spoiler> - spoiler formatting that hides the selected text
        <a href="http://www.example.com/">text</a>	Creates a hyperlink to the selected text
        """,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        tools=[{"type": "file_search"}]
    )
    return assistant
