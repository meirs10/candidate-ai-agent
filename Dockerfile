# ---------- build stage ----------
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

# Install system libraries required at build time
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        libtesseract-dev \
        poppler-utils && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency metadata first for better layer caching
COPY pyproject.toml .python-version ./
COPY uv.lock* ./

# Install production dependencies (no dev group, no editable install yet)
RUN uv sync --no-dev --no-install-project

# Copy the rest of the source code
COPY . .

# Final sync to register the project itself
RUN uv sync --no-dev

# ---------- runtime stage ----------
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

# Install only the runtime system libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr \
        poppler-utils && \
    rm -rf /var/lib/apt/lists/*

# Copy the entire app + virtual-env from builder
COPY --from=builder /app /app

# Put the venv on PATH so `streamlit` is found directly
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8501

HEALTHCHECK CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"]

ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
