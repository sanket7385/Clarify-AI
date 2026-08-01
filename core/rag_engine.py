import os


def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except Exception:
        try:
            clean = [str(a).encode('ascii', errors='replace').decode('ascii') for a in args]
            print(*clean, **kwargs)
        except Exception:
            pass


from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

from core.vector_store import build_vector_store, load_vector_store, get_retriever


def get_llm():
    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.3,
    )


def format_docs(docs):
    safe_print("\n========== RETRIEVED DOCUMENTS ==========")
    for i, doc in enumerate(docs):
        safe_print(f"\n----- Chunk {i+1} -----")
        safe_print(doc.page_content[:500])
    safe_print("\n=========================================\n")
    return "\n\n".join(doc.page_content for doc in docs)


RAG_SYSTEM_PROMPT = """
You are an expert AI Meeting Assistant.

Use ONLY the transcript context provided below.

Your responsibilities:
1. Answer questions about the meeting.
2. Summarize key ideas.
3. Explain important concepts discussed.
4. Highlight interesting insights.
5. Extract action items, decisions, risks, and lessons.

If the user asks for interesting points, key takeaways, lessons learned, or important ideas,
generate them from the transcript context.

Only say "I could not find this information in the meeting transcript."
when the transcript truly contains no relevant information.

Meeting Transcript Context:
{context}
"""


def _build_chain(retriever):
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", RAG_SYSTEM_PROMPT),
        ("human", "{question}"),
    ])
    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain


def build_rag_chain(transcript: str, collection_name: str | None = None):
    safe_print("Building Vector Store...")
    vector_store = build_vector_store(transcript, collection_name=collection_name)
    retriever = get_retriever(vector_store, k=6)
    return _build_chain(retriever)


def load_rag_chain(collection_name: str | None = None):
    safe_print("Loading existing vector store...")
    vector_store = load_vector_store(collection_name=collection_name)
    retriever = get_retriever(vector_store, k=6)
    return _build_chain(retriever)


def ask_question(rag_chain, question: str) -> str:
    safe_print(f"\nQUESTION: {question}")
    answer = rag_chain.invoke(question)
    safe_print(f"ANSWER: {answer[:200]}")
    return answer