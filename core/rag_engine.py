import os

from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

from core.vector_store import (
    build_vector_store,
    load_vector_store,
    get_retriever,
)


def get_llm():
    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.3,
    )


def format_docs(docs):
    """
    Convert retrieved documents into a single context string.
    Also print retrieved chunks for debugging.
    """

    print("\n========== RETRIEVED DOCUMENTS ==========")

    for i, doc in enumerate(docs):
        print(f"\n----- Chunk {i+1} -----")
        print(doc.page_content[:500])

    print("\n=========================================\n")

    return "\n\n".join(doc.page_content for doc in docs)


def build_rag_chain(transcript: str, collection_name: str | None = None):
    """
    Creates vector DB from transcript and builds RAG chain.
    """

    print("Building Vector Store...")

    vector_store = build_vector_store(transcript, collection_name=collection_name)

    retriever = get_retriever(
        vector_store,
        k=6
    )

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are an expert AI Meeting Assistant.

Use ONLY the transcript context provided below.

Your responsibilities:

1. Answer questions about the meeting.
2. Summarize key ideas.
3. Explain important concepts discussed.
4. Highlight interesting insights.
5. Extract action items, decisions, risks, and lessons.

If the user asks for:
- Interesting points
- Key takeaways
- Lessons learned
- Important ideas

You should generate them from the transcript context.

Only say:

"I could not find this information in the meeting transcript."

when the transcript truly contains no relevant information.

Meeting Transcript Context:
{context}
""",
            ),
            (
                "human",
                "{question}",
            ),
        ]
    )

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


def load_rag_chain(collection_name: str | None = None):
    """
    Loads existing vector DB and builds RAG chain.
    """

    print("Loading existing vector store...")

    vector_store = load_vector_store(collection_name=collection_name)

    retriever = get_retriever(
        vector_store,
        k=6
    )

    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are an expert AI Meeting Assistant.

Use ONLY the transcript context provided below.

You can:
- Answer questions
- Generate summaries
- Explain concepts
- Provide insights
- Extract action items
- Highlight important moments

If the answer is genuinely unavailable in the transcript, say:

"I could not find this information in the meeting transcript."

Meeting Transcript Context:
{context}
""",
            ),
            (
                "human",
                "{question}",
            ),
        ]
    )

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


def ask_question(rag_chain, question: str) -> str:
    """
    Ask question to RAG pipeline.
    """

    print("\n================================")
    print("QUESTION:")
    print(question)
    print("================================\n")

    answer = rag_chain.invoke(question)

    print("\n================================")
    print("ANSWER:")
    print(answer)
    print("================================\n")

    return answer