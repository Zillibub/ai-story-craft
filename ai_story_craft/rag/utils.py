import openai
from langfuse.openai import openai
from core.settings import settings

openai.api_key = settings.OPENAI_API_KEY


