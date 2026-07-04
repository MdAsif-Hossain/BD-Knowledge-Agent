FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application (includes prebuilt data/*.db for zero-setup runs)
COPY . .

# Build the SQLite databases if they are not already present
RUN python -m src.data.build_databases || true

# Render/most PaaS inject $PORT; Hugging Face Spaces (Docker SDK) expects 7860.
ENV PORT=8000
EXPOSE 8000

HEALTHCHECK CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\",8000)}/api/status', timeout=3)" || exit 1

CMD uvicorn server:app --host 0.0.0.0 --port ${PORT}
