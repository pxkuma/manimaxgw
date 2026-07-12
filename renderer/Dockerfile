# Renderer microservice
# Runs the Python/Manim video pipeline + exposes a FastAPI HTTP interface
FROM manimcommunity/manim:latest

USER root

# System deps
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps for the pipeline + API server
RUN pip install --no-cache-dir \
    edge-tts \
    numpy \
    scipy \
    fastapi \
    "uvicorn[standard]" \
    anyio

WORKDIR /app

# Copy the video pipeline and API wrapper
COPY auto_video.py .
COPY renderer_api.py .

# Internal port (not exposed to host)
EXPOSE 5050

# Start the FastAPI server
CMD ["uvicorn", "renderer_api:app", "--host", "0.0.0.0", "--port", "5050"]
