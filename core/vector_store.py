import os
import uuid
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except Exception:
        try:
            clean = [str(a).encode('ascii', errors='replace').decode('ascii') for a in args]
            print(*clean, **kwargs)
        except Exception:
            pass


CHROMA_DIR = "vector_db"
DEFAULT_COLLECTION_NAME = "default_meeting"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"}
    )


def build_vector_store(transcript: str, collection_name: str | None = None) -> Chroma:
    safe_print("Building vector Store")
    if collection_name is None:
        collection_name = f"meeting_{uuid.uuid4()}"

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(transcript)
    safe_print(f"Number of chunks: {len(chunks)}")

    if len(chunks) == 0:
        raise ValueError("No chunks created from transcript")

    docs = [
        Document(page_content=chunk, metadata={"chunk_index": i})
        for i, chunk in enumerate(chunks)
    ]

    embeddings = get_embeddings()
    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=CHROMA_DIR
    )
    return vector_store


def load_vector_store(collection_name: str | None = None) -> Chroma:
    if collection_name is None:
        collection_name = DEFAULT_COLLECTION_NAME
    embeddings = get_embeddings()
    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR
    )
    return vector_store


def get_retriever(vector_store: Chroma, k: int = 4):
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k}
    )
