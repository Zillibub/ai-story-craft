import openai
from core.settings import settings


class AssistantManager:
    def __init(self):
        self.client = openai.Client(api_key=settings.openai_api_key)

    def create_assistant(self, name: str):
        assistant = self.client.beta.assistants.create(
            model=settings.assistant_model,
        )