# Vrihi — AI Video Generator (Manim + Edge-TTS + DeepSeek)

Yo This project provides a fully automated pipeline for generating highly educational, aesthetic, YouTube-style technical explainer clips. By leveraging the **DeepSeek v3.1 (671B)** model via **Ollama**, the `edge-tts` speech synthesizer, and the **Manim** animation engine, it builds cinematic chapter-based video explanations from just a single topic prompt.

It comes with two main modes of operation:
1. **AI Prompt-to-Video Mode** (`auto_video.py`)
2. **Direct Python Script Mode** (`autorun.py`)

---

## 🏗️ Architecture & Workflow

### 1. `auto_video.py` (AI Prompt-to-Video)

This is the main driver for zero-to-video generation based on textual prompts.

**Pipeline Breakdown:**
1. **Prompt Enhancement & Curriculum Planning:** The user's raw topic is sent to DeepSeek v3.1 via Ollama, which acts as a curriculum designer — breaking the topic into 6-10 detailed chapters with visual plans, real-world examples, coordinates, and audio narration blueprints.
2. **Script & Code Generation:** For each chapter, DeepSeek generates comprehensive educational narration (10-15 sentences with examples) AND the actual Manim visualization code (strictly formatted via custom guardrails for safe rendering).
3. **Audio Synthesis (`edge-tts`):** The narration script is sent to Microsoft Edge's TTS endpoint to synthesize a pristine MP3 narration clip.
4. **Visual Rendering (`manim`):** The generated Python code is written to `media/scripts/<topic>/` and processed by the Manim build engine. The resulting MP4 visual is exported to `media/visual/<topic>/`.
5. **Merging & Synchronization:** Audio and video clips are stitched using `ffmpeg`. If there is a background track (`bg.mp3`), it is cleanly mixed into the master composition.
6. **Artifact Organization:** All intermediate and final builds are isolated within `media/<topic_name>/`.

### 2. `autorun.py` (Direct Script Mode)

This script allows you to rapidly build and concat customized, manually written Manim scene collections.
- It reads a target `.py` Python file.
- Automatically detects all classes that inherit from `Scene`.
- Executes the Manim renderer sequentially at 1080p60.
- Stitches the sequence using fast `ffmpeg` pass-throughs.

---

## 📂 Project Structure

```bash
.
├── auto_video.py        # Main AI generator script (DeepSeek + Ollama)
├── autorun.py           # Tool to automatically compile static Manim scripts
├── Dockerfile           # Manim container (no API deps, Ollama-connected)
├── docker-compose.yml   # Ollama + Vrihi services with GPU passthrough
├── .env                 # Ollama configuration (URL, model name)
├── vrihi.sh             # Interactive menu launcher
├── media/               # Master asset directory
│   ├── audio/           # Rendered speech narration mp3s
│   ├── scripts/         # Auto-generated manim python sub-scripts
│   ├── visual/          # Silent mp4 video renders from manim
│   ├── chunks/          # Chapter elements (visual + audio stitched together)
│   ├── final/           # Fully concatenated result videos
│   └── manim/           # Manim build caches
└── examples/            # Example manually written manim codes (e.g. sin.py)
```

---

## 🚀 How to Run

### Prerequisites

- **Docker** with Docker Compose v2
- **NVIDIA Container Toolkit** (for GPU passthrough to Ollama)
- Ollama model: `deepseek-v3.1:671b-cloud`

### Quick Start (Docker Compose — Recommended)

```bash
# 1. Build the Vrihi container
docker compose build

# 2. Start everything (Ollama + Vrihi)
docker compose up -d

# 3. Pull the DeepSeek model (first time only)
docker compose exec ollama ollama pull deepseek-v3.1:671b-cloud

# 4. Run the interactive pipeline
docker compose run --rm vrihi
```

### Running the AI Video Pipeline

```bash
# Via the interactive menu:
bash vrihi.sh
# Select Option 1, enter your topic

# Or directly:
docker compose run --rm --entrypoint bash vrihi -c "python auto_video.py 'Docker Basics'"
```

The script will outline 6-10 chapters, generate detailed visuals/audio with examples, and output the final video to `../Videos/production/`.

### Running the Manual Python Pipeline

```bash
# If you designed a custom Python script (e.g., examples/sin.py):
docker compose run --rm --entrypoint bash vrihi -c "python autorun.py examples/sin.py"
```

### Running Without Docker (Host Mode)

If you have Ollama running on your host machine:

```bash
# Make sure Ollama is running
ollama serve

# Set env vars
export OLLAMA_URL=http://localhost:11434/api/generate
export OLLAMA_MODEL=deepseek-v3.1:671b-cloud

# Run directly
python auto_video.py "Python Lists"
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://localhost:11434/api/generate` | Ollama API endpoint |
| `OLLAMA_MODEL` | `deepseek-v3.1:671b-cloud` | Model to use for generation |
