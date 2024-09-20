import json
from pathlib import Path
from langchain_chroma import Chroma
from langchain.vectorstores import VectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from langchain_core.documents.base import Document
from core.settings import settings
from langchain_core.runnables import RunnableParallel
from agents import ProductManager


class LangChanAgent:
    description_path: str = "description.txt"
    vectorstore_path: str = "vectorstore"

    def __init__(self, vector_store: VectorStore, description: str):
        self.llm = ChatOpenAI(model=settings.assistant_model)
        self.vector_store = vector_store
        self.retriever = self.vector_store.as_retriever()

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

    @classmethod
    def create(cls, subtitle_file: Path, agent_dir: Path):
        if not subtitle_file.exists():
            raise FileNotFoundError(f"Subtitle file not found: {subtitle_file}")
        if agent_dir.exists():
            raise FileExistsError(f"Agent folder already exists: {agent_dir}")
        agent_dir.mkdir(parents=True)

        with open(subtitle_file, 'r') as f:
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

        with open(agent_dir / cls.description_path, 'w') as f:
            f.write(description)

        return cls(vector_store=vectorstore, description=description)

    @classmethod
    def load(cls, agent_dir: Path):
        vectorstore = Chroma(
            embedding_function=OpenAIEmbeddings(),
            persist_directory=str(agent_dir / cls.vectorstore_path)
        )
        with open(agent_dir / cls.description_path, 'r') as f:
            description = f.read()
        return cls(vector_store=vectorstore, description=description)
