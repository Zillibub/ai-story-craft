import json
import ffmpeg
import shutil
from typing import Tuple, List
from pathlib import Path
from langchain_chroma import Chroma
from langchain.vectorstores import VectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from langchain_core.documents.base import Document
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from core.settings import settings
from rag.agents import ProductManager, Formatter
from langfuse.openai import openai


openai.api_key = settings.OPENAI_API_KEY


class LangChanAgent:
    metadata_path: str = "description.txt"
    vectorstore_path: str = "vectorstore"
    subtitle_raw_text_path: str = 'subtitles.txt'
    screenshot_extension: str = "png"

    def __init__(
            self,
            name: str,
            vector_store: VectorStore,
            video_path: Path,
            description: str,
            raw_text_path: Path
    ):
        self.name = name
        self.llm = ChatOpenAI(model=settings.assistant_model, openai_api_key=settings.OPENAI_API_KEY)
        self.vector_store = vector_store
        self.retriever = self.vector_store.as_retriever()
        self.video_path = video_path
        self.description = description
        self.raw_text_path = raw_text_path

        self.prompt = ChatPromptTemplate(
            messages=[HumanMessagePromptTemplate(prompt=PromptTemplate(
                input_variables=['context', 'question'], template=ProductManager.instructions
            ))]
        )

    @staticmethod
    def _format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def _contextualize(self, question: str, message_history) -> str:

        rag_chain = (
                {"history": lambda x: str(list(message_history)), "question": RunnablePassthrough()}
                | ChatPromptTemplate(
                    messages=[HumanMessagePromptTemplate(prompt=PromptTemplate(
                        input_variables=['history', 'question'], template=ProductManager.contextualize
                    ))]
                )
                | self.llm
        )

        return rag_chain.invoke(question).content

    def answer(self, question: str, message_history = None) -> str:

        if message_history:
            question = self._contextualize(question, message_history)

        rag_chain = (
                {"context": self.retriever | self._format_docs, "question": RunnablePassthrough()}
                | self.prompt
                | self.llm
        )

        return rag_chain.invoke(question).content

    def create_user_story_map(self) -> str:

        with open(self.raw_text_path, 'r') as f:
            subtitles = f.read()

        rag_chain = (
            ChatPromptTemplate.from_template(ProductManager.user_story_mapping) | self.llm | StrOutputParser()
        )

        return rag_chain.invoke({"subtitles": subtitles})

    def apply_telegram_formating(self, text: str):
        rag_chain = (
                ChatPromptTemplate.from_template(Formatter.telegram_formatting) | self.llm | StrOutputParser()
        )
        return rag_chain.invoke({"text": text})

    def apply_discord_formating(self, text: str) -> List[str]:

        parser = JsonOutputParser()
        rag_chain = (
                ChatPromptTemplate.from_template(
                    Formatter.discord_formatting,
                    partial_variables={"format_instructions": parser.get_format_instructions()}
                ) | self.llm | parser
        )
        return rag_chain.invoke({"text": text})

    def get_image(self, description: str) -> Tuple[bytes, str, str]:
        """
        Get image from video based on description
        :param description: screenshot description
        :return: [image_bytes, image_name, readable_timestamp]
        """
        docs = self.retriever.invoke(description)
        prompt = ChatPromptTemplate(
            messages=[HumanMessagePromptTemplate(prompt=PromptTemplate(
                input_variables=['description', 'context'],
                template=ProductManager.get_image_timestamp
            ))]
        )
        rag_chain = (
                {"description": RunnablePassthrough()}
                | prompt
                | self.llm
        )

        image_timestamp = rag_chain.invoke(
            description + ", Subtitles: " + "\n\n".join(doc.page_content for doc in docs)
        ).content

        # Convert timestamp to readable format
        minutes = int(float(image_timestamp)) // 60
        seconds = int(float(image_timestamp)) % 60
        readable_timestamp = f"{minutes:02d}:{seconds:02d}"

        prompt = ChatPromptTemplate(
            messages=[HumanMessagePromptTemplate(prompt=PromptTemplate(
                input_variables=['description', 'context'],
                template=ProductManager.get_image_name
            ))]
        )
        rag_chain = (
                {"description": RunnablePassthrough()}
                | prompt
                | self.llm
        )
        image_file_name = rag_chain.invoke(description).content + f".{self.screenshot_extension}"

        process =(
            ffmpeg
            .input(self.video_path, ss=image_timestamp)
            .output('pipe:', vframes=1, format='image2', vcodec='png')
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )
        image_bytes, _ = process.communicate()

        return image_bytes, image_file_name, readable_timestamp

    @classmethod
    def create(
            cls,
            name: str,
            video_path: Path,
            subtitle_file_path: Path,
            agent_dir: Path,
            overwrite: bool = False
    ):
        if not subtitle_file_path.exists():
            raise FileNotFoundError(f"Subtitle file not found: {subtitle_file_path}")
        if agent_dir.exists():
            if overwrite:
                shutil.rmtree(agent_dir)
            else:
                raise FileExistsError(f"Agent folder already exists: {agent_dir}")
        agent_dir.mkdir(parents=True)

        with open(subtitle_file_path, 'r') as f:
            subtitles = json.load(f)

        segments = [{
            'id': entry['id'],
            'start': round(entry['start']),
            'end': round(entry['end']),
            'text': entry['text']} for entry in subtitles['segments']]

        docs = [Document(page_content=str(segments))]

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY),
            persist_directory=str(agent_dir / cls.vectorstore_path)
        )

        llm = ChatOpenAI(model=settings.assistant_model, openai_api_key=settings.OPENAI_API_KEY)
        description = llm.invoke([["human", ProductManager.assistant_description_prompt]]).content

        with open(agent_dir / cls.metadata_path, 'w') as f:
            json.dump({
                'name': name,
                'description': description,
                'video_path': str(video_path)
            }, f)

        with open(agent_dir / cls.subtitle_raw_text_path, 'w') as f:
            f.write(subtitles['text'])

        return cls(
            name=name,
            vector_store=vectorstore,
            description=description,
            video_path=video_path,
            raw_text_path=agent_dir / cls.subtitle_raw_text_path
        )

    @classmethod
    def load(cls, agent_dir: Path):
        vectorstore = Chroma(
            embedding_function=OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY),
            persist_directory=str(agent_dir / cls.vectorstore_path)
        )
        with open(agent_dir / cls.metadata_path, 'r') as f:
            metadata = json.load(f)
            description = metadata['description']
            name = metadata['name']
            video_path = Path(metadata['video_path'])

        return cls(
            name=name,
            vector_store=vectorstore,
            description=description,
            video_path=video_path,
            raw_text_path=agent_dir / cls.subtitle_raw_text_path
        )
