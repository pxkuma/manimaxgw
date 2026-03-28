# Start with Manim's official fat image
FROM manimcommunity/manim:latest

# Switch to root to install packages
USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (Ollama-only pipeline, no external API deps)
RUN pip install --no-cache-dir \
    edge-tts \
    numpy \
    scipy

# Set working directory
WORKDIR /manim

# Copy vrihi.sh and make it executable
COPY vrihi.sh /usr/local/bin/vrihi.sh
RUN sed -i 's/\r$//' /usr/local/bin/vrihi.sh && chmod +x /usr/local/bin/vrihi.sh

# Default entrypoint: vrihi.sh (interactive menu-driven)
ENTRYPOINT ["/usr/local/bin/vrihi.sh"]
