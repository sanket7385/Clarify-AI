# ============================================================================
# Stage 1 — Builder: install all Python dependencies (with build tools)
# ============================================================================
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build-time system deps (these stay ONLY in this stage)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# ── KEY OPTIMISATION ──────────────────────────────────────────────────────────
# Install CPU-only PyTorch first (skips ~5 GB of CUDA libraries),
# then install the rest of the requirements.
RUN pip install --no-cache-dir \
        torch torchaudio \
        --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt && \
    # Remove GPU-only transitive deps that are useless on CPU (~700 MB)
    pip uninstall -y triton || true && \
    # Strip test suites, __pycache__, and .dist-info to reclaim space
    find /usr/local/lib/python3.11/site-packages \
        \( -type d -name "__pycache__" -o -type d -name "tests" -o -type d -name "test" \) \
        -exec rm -rf {} + 2>/dev/null || true

# ============================================================================
# Stage 2 — Runtime: lean image with only what's needed to run the app
# ============================================================================
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    HF_HOME=/app/data/.cache \
    TORCH_HOME=/app/data/.cache

WORKDIR /app

# Runtime-only system dependencies (no build-essential!)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/share/doc /usr/share/man /usr/share/info

# Copy pre-built Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create runtime directories
RUN mkdir -p /app/data /app/vector_db /app/temp /app/downloads

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true", \
     "--server.maxUploadSize=500"]
