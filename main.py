from dotenv import load_dotenv
import os
import uuid
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()


def run_pipeline(source: str, language: str = "english") -> dict:
    if not os.getenv("MISTRAL_API_KEY"):
        raise RuntimeError("MISTRAL_API_KEY is not set in environment or .env file.")
    if language.lower() == "hinglish" and not os.getenv("SARVAM_API_KEY"):
        raise RuntimeError("SARVAM_API_KEY is not set, required for hinglish.")

    chunks = process_input(source)
    try:
        transcript = transcribe_all(chunks, language)

        for chunk in chunks:
            try:
                if os.path.exists(chunk):
                    os.remove(chunk)
            except Exception:
                pass

        title = generate_title(transcript)
        summary = summarize(transcript)
        action_item = extract_action_items(transcript)
        decisions = extract_key_decisions(transcript)
        questions = extract_questions(transcript)

        collection_name = f"meeting_{uuid.uuid4()}"
        rag_chain = build_rag_chain(transcript, collection_name=collection_name)

        return {
            "title": title,
            "transcript": transcript,
            "summary": summary,
            "action_items": action_item,
            "key_decisions": decisions,
            "open_questions": questions,
            "rag_chain": rag_chain,
        }
    except Exception as err:
        for chunk in chunks:
            try:
                if os.path.exists(chunk):
                    os.remove(chunk)
            except Exception:
                pass
        raise err


if __name__ == "__main__":
    source = input("Enter YouTube URL or local file path: ").strip()
    language = input("Language (english/hinglish): ").strip() or "english"
    result = run_pipeline(source, language)

    print(f"\nTitle: {result['title']}")
    print(f"\nSummary:\n{result['summary']}")
    print(f"\nAction Items:\n{result['action_items']}")
    print(f"\nKey Decisions:\n{result['key_decisions']}")
    print(f"\nOpen Questions:\n{result['open_questions']}")

    print("\nChat with your meeting (type 'exit' to quit)\n")
    rag_chain = result["rag_chain"]
    while True:
        question = input("You: ").strip()
        if question.lower() in ["exit", "quit", "q"]:
            break
        if not question:
            continue
        answer = ask_question(rag_chain, question)
        print(f"\nAssistant: {answer}\n")