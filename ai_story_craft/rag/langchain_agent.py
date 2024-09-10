from typing import Tuple
from pathlib import Path
from langchain_chroma import Chroma
from langchain.vectorstores import VectorStore
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader
from langchain_openai import ChatOpenAI
from core.settings import settings
from agents import ProductManager


class LangChanAgent:

    def __init__(self, vector_store: VectorStore, description: str):
        self.llm = ChatOpenAI(model=settings.assistant_model)
        self.vector_store = vector_store

    @classmethod
    def create(cls, subtitle_file: Path, agent_dir: Path):
        if not subtitle_file.exists():
            raise FileNotFoundError(f"Subtitle file not found: {subtitle_file}")
        if agent_dir.exists():
            raise FileExistsError(f"Vector store already exists: {agent_dir}")
        agent_dir.mkdir(parents=True)

        loader = TextLoader(subtitle_file)
        docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)
        vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=OpenAIEmbeddings(),
            persist_directory=str(agent_dir / 'vectorstore')
        )

        llm = ChatOpenAI(model=settings.assistant_model)
        description = llm.invoke([["human", ProductManager.assistant_description_prompt]]).content

        with open(agent_dir / 'description.txt', 'w') as f:
            f.write(description)

        return cls(vector_store=vectorstore, description=description)

    @classmethod
    def load(cls, agent_dir: Path):
        vectorstore = Chroma(embedding_function=OpenAIEmbeddings(), persist_directory=str(agent_dir / 'vectorstore'))
        with open(agent_dir / 'description.txt', 'r') as f:
            description = f.read()
        return cls(vector_store=vectorstore, description=description)
