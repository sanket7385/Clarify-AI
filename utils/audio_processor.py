import yt_dlp  # type: ignore[import-untyped]
from pydub import AudioSegment
import os
import uuid
import time


def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except Exception:
        try:
            clean = [str(a).encode('ascii', errors='replace').decode('ascii') for a in args]
            print(*clean, **kwargs)
        except Exception:
            pass


DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def save_uploaded_file(uploaded_file) -> str:
    file_ext = os.path.splitext(uploaded_file.name)[1]
    save_path = os.path.join(DOWNLOAD_DIR, f"uploaded_{uuid.uuid4()}{file_ext}")
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return save_path


def download_youtube_audio(url: str, max_attempts: int = 3) -> str:
    file_id = f"yt_{uuid.uuid4()}"
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "128",
            }
        ],
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
        "retries": 10,
        "fragment_retries": 10,
        "file_access_retries": 5,
        "extractor_args": {
            "youtube": {
                "player_client": ["android_vr"]
            }
        },
    }

    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            safe_print(f"Downloading YouTube audio (Attempt {attempt}/{max_attempts})...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
            break
        except Exception as err:
            last_error = err
            safe_print(f"[WARNING] YouTube download attempt {attempt} failed: {err}")
            if attempt == max_attempts:
                raise RuntimeError(
                    f"Failed to download YouTube audio after {max_attempts} attempts. "
                    f"Network error: {err}"
                ) from err
            time.sleep(2)

    expected_wav = os.path.join(DOWNLOAD_DIR, f"{file_id}.wav")
    if not os.path.exists(expected_wav):
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(file_id) and f.endswith(".wav"):
                return os.path.join(DOWNLOAD_DIR, f)
        raise FileNotFoundError(f"Downloaded audio file for {url} not found at {expected_wav}")
    return expected_wav


def convert_to_wav(input_path: str) -> str:
    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio: AudioSegment = AudioSegment.from_file(input_path)  # type: ignore[assignment]
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")
    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list[str]:
    audio: AudioSegment = AudioSegment.from_wav(wav_path)  # type: ignore[assignment]
    chunk_ms = chunk_minutes * 60 * 1000
    chunks: list[str] = []
    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk: AudioSegment = audio[start : start + chunk_ms]  # type: ignore[assignment]
        chunk_path = f"{wav_path}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)
    return chunks


def process_input(source: str) -> list:
    if source.startswith("http://") or source.startswith("https://"):
        safe_print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        safe_print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    safe_print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    safe_print(f"Audio ready - {len(chunks)} chunk(s) created.")

    try:
        if os.path.exists(wav_path):
            os.remove(wav_path)
            safe_print(f"Removed intermediate audio file: {wav_path}")
    except Exception as e:
        safe_print(f"Failed to remove intermediate file {wav_path}: {e}")

    return chunks
