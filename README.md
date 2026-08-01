# 🎬 ScribeFlow AI — Intelligent Meeting Assistant & RAG Engine

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-121212?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain.com)
[![Mistral AI](https://img.shields.io/badge/Mistral_AI-FF7000?style=for-the-badge&logo=mistral&logoColor=white)](https://mistral.ai)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0052CC?style=for-the-badge&logo=sqlite&logoColor=white)](https://trychroma.com)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

> **ScribeFlow AI** is a state-of-the-art AI-powered meeting intelligence platform. It transcribes audio from YouTube videos or local file uploads, synthesizes structured executive summaries, extracts actionable tasks & decisions, and allows users to interactively chat with meeting transcripts using Retrieval-Augmented Generation (RAG).

---

## ✨ Key Features

- **🎙️ Multi-Engine Speech-to-Text**:
  - **Whisper AI**: Ultra-fast, high-accuracy English transcription.
  - **Sarvam AI**: Specialized Hinglish (Hindi + English) speech translation.
- **📝 Automated Meeting Insights**:
  - Executive Summaries (Map-Reduce LCEL pipeline).
  - Actionable Task Assignments (Task, Owner, Deadline).
  - Key Decisions & Unresolved Open Questions.
- **💬 Interactive RAG Meeting Chat**:
  - Talk to your meeting transcript in real-time.
  - Vector similarity retrieval powered by **HuggingFace Embeddings** and **ChromaDB**.
  - Powered by **Mistral AI** (`mistral-small-latest`).
- **⚡ Hardened Performance & Resilience**:
  - Robust YouTube downloader with fallback mechanisms.
  - Deterministic UUID audio management & auto-cleanup.
- **🐳 Enterprise Containerization**:
  - Fully Dockerized with multi-stage builds and persistent vector DB volumes.

---

## 🏗️ System Architecture

```
                               ┌─────────────────────────┐
                               │  YouTube URL / Upload   │
                               └────────────┬────────────┘
                                            │
                                  [ Audio Processor ]
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
            [ OpenAI Whisper ]                             [ Sarvam AI STT ]
            (English Engine)                               (Hinglish Engine)
                     │                                             │
                     └──────────────────────┬──────────────────────┘
                                            │
                                   [ Transcript Text ]
                                            │
          ┌─────────────────────────────────┼─────────────────────────────────┐
          ▼                                 ▼                                 ▼
   [ Summarizer ]                   [ Extractor ]                   [ Vector Store ]
  (Map-Reduce LCEL)         (Action Items, Decisions, Qs)        (ChromaDB + Embeddings)
          │                                 │                                 │
          └─────────────────────────────────┼─────────────────────────────────┘
                                            │
                                            ▼
                               [ Interactive Streamlit App ]
                                (RAG Chat with Meeting)
```

---

## 🚀 Quick Start Guide

### 1. Clone Repository & Setup Environment

```bash
git clone https://github.com/sanket7385/Clarify-AI.git
cd Clarify-AI
```

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```ini
# Required: Mistral AI API Key
MISTRAL_API_KEY=your_mistral_api_key_here

# Required only for Hinglish Speech-to-Text
SARVAM_API_KEY=your_sarvam_api_key_here

# Optional Configurations
WHISPER_MODEL=tiny
SARVAM_STT_MODEL=saaras:v2.5
```

### 3. Run Locally

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 🐳 Docker Deployment

To build and run ScribeFlow AI inside a Docker container:

```bash
# Build and launch using Docker Compose
docker compose up --build -d
```

The containerized app will be available at `http://localhost:8501`.

---

## 🔑 Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `MISTRAL_API_KEY` | **Yes** | — | API key for Mistral AI LLM |
| `SARVAM_API_KEY` | Optional | — | API key for Sarvam AI (Hinglish STT) |
| `WHISPER_MODEL` | No | `tiny` | Whisper model size (`tiny`, `base`, `small`) |
| `SARVAM_STT_MODEL` | No | `saaras:v2.5` | Sarvam STT model identifier |

---

## 🛠️ Tech Stack

- **Frontend / UI**: Streamlit
- **LLM & RAG**: LangChain, Mistral AI (`mistral-small-latest`)
- **Vector Database**: ChromaDB
- **Embeddings**: HuggingFace (`all-MiniLM-L6-v2`)
- **Speech-to-Text**: OpenAI Whisper, Sarvam AI
- **Media Processing**: `yt-dlp`, `pydub`, `ffmpeg`

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
