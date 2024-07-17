import openai
from pathlib import Path
from core.settings import settings


class AssistantManager:
    def __init(self):
        self.client = openai.Client(api_key=settings.openai_api_key)

    def create_assistant(
            self,
            name: str,
            subtitle_file: Path,
    ):
        if not subtitle_file.exists():
            raise FileNotFoundError(f"Subtitle file not found: {subtitle_file}")

        vector_store = self.client.beta.vector_stores.create(name=subtitle_file.stem)

        # Use the upload and poll SDK helper to upload the files, add them to the vector store,
        # and poll the status of the file batch for completion.
        file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, files=[open(subtitle_file, "rb")]
        )
        print(file_batch.status)
        print(file_batch.file_counts)

        assistant = self.client.beta.assistants.create(
            model=settings.assistant_model,
            description=f"Assistant for {name}",
            instructions="""You are a senior product manager who creates a user story for a new feature.
            Create the user story based only on provided information without adding any additional details. 
            """,
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        )

