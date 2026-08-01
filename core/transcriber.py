import whisper
import os
import requests
from pydub import AudioSegment


def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except Exception:
        try:
            clean = [str(a).encode('ascii', errors='replace').decode('ascii') for a in args]
            print(*clean, **kwargs)
        except Exception:
            pass


SARVAM_PIECE_SECONDS = 25
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "tiny")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")

_model = None
_model_name = None


def load_model(model_name: str | None = None):
    global _model, _model_name
    target_model = model_name or os.getenv("WHISPER_MODEL", "tiny")
    if _model is None or _model_name != target_model:
        safe_print(f"Loading Whisper model: {target_model} ...")
        _model = whisper.load_model(target_model)
        _model_name = target_model
        safe_print("Whisper model loaded.")
    return _model


def transcribe_chunk_whisper(chunk_path: str, model_name: str | None = None) -> str:
    model = load_model(model_name)
    result = model.transcribe(chunk_path, task="transcribe", fp16=False)
    return result["text"]


def _send_to_sarvam(piece_path: str) -> str:
    key = os.getenv("SARVAM_API_KEY") or SARVAM_API_KEY
    if not key:
        raise RuntimeError("SARVAM_API_KEY is not set in environment or .env file.")

    headers: dict[str, str] = {"api-subscription-key": key}
    with open(piece_path, "rb") as f:
        files = {"file": (os.path.basename(piece_path), f, "audio/wav")}
        data = {"model": SARVAM_MODEL, "with_diarization": "false"}
        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )

    if not response.ok:
        safe_print(f"[ERROR] Sarvam returned {response.status_code}")
        safe_print(f"Response body: {response.text}")
        response.raise_for_status()

    return response.json().get("transcript", "")


def transcribe_chunk_sarvam(chunk_path: str) -> str:
    key = os.getenv("SARVAM_API_KEY") or SARVAM_API_KEY
    if not key:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / .env")

    audio: AudioSegment = AudioSegment.from_wav(chunk_path)  # type: ignore[assignment]
    piece_ms = SARVAM_PIECE_SECONDS * 1000
    full_text = ""
    total_pieces = max(1, (len(audio) + piece_ms - 1) // piece_ms)

    for i, start in enumerate(range(0, len(audio), piece_ms)):
        piece: AudioSegment = audio[start: start + piece_ms]  # type: ignore[assignment]
        piece_path = f"{chunk_path}_sv_{i}.wav"
        piece.export(piece_path, format="wav")
        try:
            safe_print(f"  -> Sarvam piece {i + 1}/{total_pieces} ...")
            piece_transcript = _send_to_sarvam(piece_path)
            full_text += piece_transcript + " "
        except Exception as err:
            safe_print(f"[ERROR] Transcribing Sarvam piece {i + 1}/{total_pieces}: {err}")
            raise err
        finally:
            if os.path.exists(piece_path):
                try:
                    os.remove(piece_path)
                except Exception as ex:
                    safe_print(f"Warning: could not delete piece file {piece_path}: {ex}")

    return full_text.strip()


def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    if language.lower() == "hinglish":
        return transcribe_chunk_sarvam(chunk_path)
    return transcribe_chunk_whisper(chunk_path)


def transcribe_all(chunks: list, language: str = "english", progress_callback=None) -> str:
    full_transcript = ""
    engine = "Sarvam AI" if language.lower() == "hinglish" else "Whisper"
    safe_print(f"Using {engine} for transcription.")

    for i, chunk in enumerate(chunks):
        safe_print(f"Transcribing chunk {i + 1}/{len(chunks)}...")
        if progress_callback:
            try:
                progress_callback(i + 1, len(chunks))
            except Exception as e:
                safe_print(f"Progress callback error: {e}")

        text = transcribe_chunk(chunk, language=language)
        safe_print(f"Chunk {i+1} transcript length: {len(text)}")
        full_transcript += text + " "

    safe_print("Transcription complete.")
    safe_print("Final transcript length:", len(full_transcript))
    return full_transcript.strip()
