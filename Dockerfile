# Start with Manim's official fat image
FROM manimcommunity/manim:latest

# Switch to root to install packages
USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install all Python dependencies for AI, TTS, and Math
RUN pip install --no-cache-dir \
    openai \
    google-genai \
    edge-tts \
    numpy \
    scipy

# Set working directory
WORKDIR /manim

# We REMOVE the ENTRYPOINT here so the container acts like a raw Ubuntu 
# environment. This allows us to run different scripts on demand!
