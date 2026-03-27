# AI Video Generator (Manim + Edge-TTS)

This project provides a fully automated pipeline for generating highly educational, aesthetic, YouTube-style technical explainer clips. By leveraging AI language models, the `edge-tts` speech synthesizer, and the `Manim` animation engine, it builds cinematic chapter-based video explanations from just a single topic prompt. 

It comes with two main modes of operation:
1. **AI Prompt-to-Video Mode** (`auto_video.py`)
2. **Direct Python Script Mode** (`autorun.py`)

---

## 🏗️ Architecture & Workflow

### 1. `auto_video.py` (AI Prompt-to-Video)
This is the main driver for zero-to-video generation based primarily on textual prompts.

**Pipeline Breakdown:**
1. **Planning System:** The system asks an LLM (via the GitHub Models GPT-4o API, falling back to Gemini 2.0 Flash) to act as a curriculum designer, dynamically breaking down the provided "Topic" into exactly three logical chapter titles.
2. **Script & Code Generation:** For each chapter, the LLM generates a cohesive educational script (the narration) AND the actual Manim visualization code (strictly formatted to render correctly via custom guardrails).
3. **Audio Synthesis (`edge-tts`):** The narrator script is securely sent to Microsoft Edge's TTS endpoint to synthesize a pristine MP3 narration clip.
4. **Visual Rendering (`manim`):** The generated python code is written to `media/scripts/<topic>/` and processed by the Manim build engine. The resulting MP4 visual is exported to `media/visual/<topic>/`.
5. **Merging & Synchronization:** Audio and Video clips are stitched directly using `ffmpeg`. If there is a background track (`bg.mp3`), it is cleanly mixed into the master composition without dropping standard formats. 
6. **Artifact Organization:** All intermediate and final builds are carefully isolated within `media/{topic_name}`.

### 2. `autorun.py` (Direct Script Mode)
This script allows you to rapidly build and concat customized, manually written Manim scene collections. 
- It reads a target `.py` python file.
- Automatically detects all classes that inherit from `Scene`.
- Executes the Manim renderer sequentially at 1080p60.
- Stitches the sequence beautifully using fast `ffmpeg` pass-throughs.

---

## 📂 Project Structure

```bash
.
├── auto_video.py        # Main AI generator script 
├── autorun.py           # Tool to automatically compile static python Manim scripts
├── Dockerfile           # For running isolation in Docker 
├── .env                 # Environment credentials (API keys)
├── media/               # Master asset directory
│   ├── audio/           # Rendered speech narration mp3s 
│   ├── scripts/         # Auto-generated manim python sub-scripts 
│   ├── visual/          # Silent mp4 video renders from manim
│   ├── chunks/          # Chapter elements (visual + audio stitched together)
│   ├── final/           # Fully concatenated result videos
│   └── manim/           # Manim build caches
├── examples/            # Example manually written manim codes (e.g. sin.py)
├── outputs/             # Miscellaneous root finalized generations
├── archive/             # Old backups and reference copies
└── logs/                # Stdout / compilation error logs
```

---

## 🚀 How to Run

### Prerequisites
Make sure dependencies are installed (e.g., in a virtual environment). Core tools requirements:
* `manim` (ManimCommunity version)
* `ffmpeg` (Required on system PATH for video and audio stitching operations)
* Python packages: `openai`, `google-genai`, `edge-tts`, `asyncio`

Make sure your API keys are provided securely in the environment:
```bash
export GITHUB_TOKEN="<your_github_token>"
export GEMINI_API_KEY="<your_gemini_key>"
```

### Running the AI Video Pipeline
To generate a video autonomously from a conceptual prompt, simply run:
```bash
python auto_video.py "Docker Basics"
```
The script will outline the 3 chapters, generate the visuals/audio, and organize output into the `media/Docker_Basics/` directory. Check `media/final/Docker_Basics/final_production.mp4` for the culmination.

### Running the Manual Python Pipeline
If you designed a custom python script (e.g., `examples/sin.py`):
```bash
python autorun.py examples/sin.py
```
This produces the fully rendered file inside your media directory gracefully.
