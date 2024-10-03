import json
import ffmpeg
import shutil
from pathlib import Path
from langchain_chroma import Chroma
from langchain.vectorstores import VectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from langchain_core.documents.base import Document
from core.settings import settings
from agents import ProductManager


class LangChanAgent:
    metadata_path: str = "description.txt"
    vectorstore_path: str = "vectorstore"

    def __init__(
            self,
            name: str,
            vector_store: VectorStore,
            video_path: Path,
            description: str
    ):
        self.name = name
        self.llm = ChatOpenAI(model=settings.assistant_model)
        self.vector_store = vector_store
        self.retriever = self.vector_store.as_retriever()
        self.video_path = video_path
        self.description = description

        self.prompt = ChatPromptTemplate(
            messages=[HumanMessagePromptTemplate(prompt=PromptTemplate(
                input_variables=['context', 'question'], template=ProductManager.instructions
            ))]
        )

    @staticmethod
    def _format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    def answer(self, question: str) -> str:
        rag_chain = (
                {"context": self.retriever | self._format_docs, "question": RunnablePassthrough()}
                | self.prompt
                | self.llm
        )

        return rag_chain.invoke(question).content

    def get_image_timestamp(self, description: str) -> str:
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
        return rag_chain.invoke(description + ", Subtitles: " + "\n\n".join(doc.page_content for doc in docs)).content

    def get_image(self, description: str) -> bytes:
        timestamp = float(self.get_image_timestamp(description))

        process =(
            ffmpeg
            .input(self.video_path, ss=timestamp)
            .output('pipe:', vframes=1, format='image2', vcodec='png')
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )
        image_bytes, _ = process.communicate()

        return image_bytes

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
            embedding=OpenAIEmbeddings(),
            persist_directory=str(agent_dir / cls.vectorstore_path)
        )

        llm = ChatOpenAI(model=settings.assistant_model)
        description = llm.invoke([["human", ProductManager.assistant_description_prompt]]).content

        with open(agent_dir / cls.metadata_path, 'w') as f:
            json.dump({
                'name': name,
                'description': description,
                'video_path': str(video_path)
            }, f)

        return cls(
            name=name,
            vector_store=vectorstore,
            description=description,
            video_path=video_path
        )

    @classmethod
    def load(cls, agent_dir: Path):
        vectorstore = Chroma(
            embedding_function=OpenAIEmbeddings(),
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
            video_path=video_path
        )
