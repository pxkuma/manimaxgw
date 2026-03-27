import os
import sys
import json
import asyncio
import subprocess
import re
import edge_tts
from google import genai
from openai import OpenAI

# --- 1. CONFIGURATION ---
if len(sys.argv) < 2:
    print("❌ Error: You forgot to provide a topic!")
    sys.exit(1)

TOPIC = sys.argv[1]

# Create safe topic name for folders
SAFE_TOPIC = re.sub(r'[^a-zA-Z0-9_\-]', '_', TOPIC.strip()).strip('_')
if not SAFE_TOPIC:
    SAFE_TOPIC = "default_topic"

# Setup directories
DIRS = {
    "scripts": f"media/scripts/{SAFE_TOPIC}",
    "audio": f"media/audio/{SAFE_TOPIC}",
    "visual": f"media/visual/{SAFE_TOPIC}",
    "chunks": f"media/chunks/{SAFE_TOPIC}",
    "final": f"media/final/{SAFE_TOPIC}",
    "manim": f"media/manim/{SAFE_TOPIC}"
}

for d in DIRS.values():
    os.makedirs(d, exist_ok=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

gh_client = OpenAI(base_url="https://models.inference.ai.azure.com", api_key=GITHUB_TOKEN)
gem_client = genai.Client(api_key=GEMINI_KEY)

VOICE = "en-GB-RyanNeural"

def clean_json(text):
    return text.replace('```json', '').replace('```python', '').replace('```', '').strip()

def get_ai_response(prompt):
    try:
        print("[*] Consulting GPT-4o via GitHub Models...")
        response = gh_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return clean_json(response.choices[0].message.content)
    except Exception as e:
        print(f"[!] GPT-4o failed: {e}. Falling back to Gemini 2.0 Flash...")
        res = gem_client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        return clean_json(res.text)

# --- 2. PIPELINE FUNCTIONS ---

def get_chapters(topic):
    print(f"[*] Planning structure for: {topic}...")
    prompt = f"""Act as an expert curriculum designer. If the user's topic '{topic}' is a single word or short phrase, expand this concept into 3 highly detailed, specific sub-topics.

Examples of good expansions:
- "Python" → ["Python Syntax Basics", "Object-Oriented Python", "Python in Data Science"]
- "Docker" → ["Container Fundamentals", "Docker Networking", "Docker Compose Orchestration"]
- "Banking" → ["Core Banking Systems", "Payment Processing", "Risk Management"]

Output exactly 3 short chapter titles as a raw JSON array of strings ONLY. No extra text."""
    return json.loads(get_ai_response(prompt))

MANIM_PROMPT_TEMPLATE = """
You are an expert Manim (Community Edition v0.18) animator and top-tier tech explainer.
Create a highly visual, diagram-focused technical scene for chapter "{chapter_title}" from topic "{topic}".

STRICT OUTPUT FORMAT — respond with ONLY raw JSON, no markdown, no explanation:
{{
  "audio_script": "Your narration here",
  "manim_code": "<full python code here>"
}}

CRITICAL AUDIO_SCRIPT RULES:
- Write 6-8 clear, educational sentences that explain the concept step by step
- Act like a confident teacher explaining to students - clear, engaging, informative
- STRICTLY plain text narration only - absolutely NO emojis, markdown, bullets, or code formatting
- NO special math symbols, hashtags, or unusual punctuation that breaks TTS
- Use simple punctuation: periods and commas only
- Focus on explaining WHAT the concept is, HOW it works, and WHY it matters
- Make it conversational and easy to understand

MANIM CODE REQUIREMENTS:
- Class name MUST be: GeneratedScene
- Must start with: from manim import *
- Inherit from Scene
- End with self.wait(3)
- Total animation runtime: 18-22 seconds
- Create VISUAL DIAGRAMS with shapes, arrows, and labeled components - NOT walls of text

ABSOLUTE RULES - NO TEXT OVERLAYS:
- DO NOT create title cards or persistent text labels that stay on screen
- DO NOT use corner text or fixed position text overlays
- Text should ONLY be used as small labels inside diagram components (2-3 words max per label)
- All text must be part of animated diagram elements that appear and disappear with the scene flow
- Focus on SHAPES, BOXES, ARROWS, FLOWS - not paragraphs or explanations in text form
- The narration explains the concept - visuals should show structure and relationships

MANDATORY LAYOUT SAFETY (CRITICAL - VIOLATIONS WILL CAUSE OUT OF BOUNDS):
1. FORBIDDEN: FRAME_WIDTH, FRAME_HEIGHT (deprecated) - use config.frame_width and config.frame_height
2. FORBIDDEN: .shift(), .to_edge(), .to_corner(), or manual coordinates like [0,2,0]
3. MANDATORY LAYOUT PATTERN (follow exactly):
   a) Create all visual elements (boxes, arrows, labels)
   b) Group them: master_group = VGroup(element1, element2, element3, ...)
   c) Arrange vertically: master_group.arrange(DOWN, buff=0.5)
   d) Scale to fit safely: master_group.scale_to_fit_width(config.frame_width - 3)
   e) Center everything: master_group.move_to(ORIGIN)
4. EVERY element must be inside the master_group - no exceptions
5. Keep font_size <= 28 for labels, use max width=8 for any text to prevent overflow
6. Test bounds: all objects must fit in a (config.frame_width - 3) x (config.frame_height - 2) safe zone

VISUAL STYLE:
- BLACK background with color-coded shapes: BLUE_D, TEAL_D, GREEN_D, GOLD_D, RED_D, PURPLE_D, WHITE
- Create structured diagrams: containers, layers, flows, processes, data paths
- Use smooth transitions: DrawBorderThenFill, FadeIn, GrowFromCenter, Create
- Keep animations purposeful and timed to match narration length (18-22 sec total)
- Brief highlights with SurroundingRectangle to emphasize key parts

BUILDING BLOCKS (adapt to your concept):

# Labeled container:
box = Rectangle(width=3.5, height=2, color=BLUE_D, fill_opacity=0.2, stroke_width=3)
label = Text("Core", font_size=24, color=BLUE_D).move_to(box)
container = VGroup(box, label)

# Multi-layer structure:
layers = VGroup(*[
    Rectangle(width=4, height=0.8, color=c, fill_opacity=0.25, stroke_width=2)
    for c in [BLUE_D, TEAL_D, GREEN_D]
]).arrange(DOWN, buff=0.1)

# Arrow flow:
start_box = Rectangle(width=2, height=1, color=GREEN_D, fill_opacity=0.3)
end_box = Rectangle(width=2, height=1, color=RED_D, fill_opacity=0.3)
boxes = VGroup(start_box, end_box).arrange(RIGHT, buff=2)
arrow = Arrow(start_box.get_right(), end_box.get_left(), color=WHITE, buff=0.2)
flow = VGroup(boxes, arrow)

# Data movement:
particle = Dot(color=GOLD_D, radius=0.15)
self.play(particle.animate.move_to(target_position), run_time=1.2)
self.play(FadeOut(particle, scale=0.5), run_time=0.3)

# Safe composition (ALWAYS USE THIS PATTERN):
master_group = VGroup(element1, element2, element3)  # Add ALL scene elements
master_group.arrange(DOWN, buff=0.6)  # Arrange vertically with spacing
master_group.scale_to_fit_width(config.frame_width - 3)  # Safe scaling
master_group.move_to(ORIGIN)  # Center on canvas
self.play(LaggedStart(*[FadeIn(obj) for obj in master_group], lag_ratio=0.3))
self.wait(2)

Now create a COMPLETE GeneratedScene for "{chapter_title}" (topic: "{topic}"):
- Write clear educational narration (6-8 sentences)
- Build a visual diagram with shapes and minimal text labels
- Use the safe composition pattern to keep everything in bounds
- NO title cards, NO text overlays, NO walls of text
- Make it clean, visual, and perfectly centered
"""

def get_chapter_content(chapter_title, topic):
    print(f"[*] Generating cinematic scene for: {chapter_title}...")
    prompt = MANIM_PROMPT_TEMPLATE.format(chapter_title=chapter_title, topic=topic)
    raw = get_ai_response(prompt)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find('{')
        end = raw.rfind('}') + 1
        if start == -1 or end == 0:
            raise ValueError(f"Could not extract JSON from AI response: {raw[:300]}")
        data = json.loads(raw[start:end])

    return data["audio_script"], data["manim_code"]

def validate_and_fix_manim(code, index):
    """Ensure manim code is safe to render and follows layout rules."""
    # Fix class name
    if "class GeneratedScene" not in code:
        for wrong in ["class Scene(", "class MyScene(", "class AnimatedScene(", "class ExplainerScene("]:
            if wrong in code:
                code = code.replace(wrong, "class GeneratedScene(")
                break

    # Ensure import
    if "from manim import" not in code:
        code = "from manim import *\n" + code

    # Ensure wait at end
    if "self.wait" not in code:
        code = code.rstrip() + "\n        self.wait(3)\n"

    # Anti-hallucination code replacements
    code = code.replace("FRAME_WIDTH", "config.frame_width")
    code = code.replace("FRAME_HEIGHT", "config.frame_height")
    code = code.replace("FadeIn(self.mobjects)", "pass")

    # Remove forbidden positioning methods that cause out-of-bounds
    forbidden_patterns = [
        ".to_corner(UL)", ".to_corner(UR)", ".to_corner(DL)", ".to_corner(DR)",
        "to_corner(", "to_edge(", ".shift(UP", ".shift(DOWN", ".shift(LEFT", ".shift(RIGHT"
    ]

    for pattern in forbidden_patterns:
        if pattern in code:
            print(f"[!] Warning: Found forbidden pattern '{pattern}' in scene_{index}, removing...")
            # Replace with safe alternatives
            code = code.replace(".to_corner(UL)", "")
            code = code.replace(".to_corner(UR)", "")
            code = code.replace(".to_corner(DL)", "")
            code = code.replace(".to_corner(DR)", "")
            # Note: More complex patterns like .shift() with values are harder to auto-fix
            # but the warning will alert us to the issue

    return code

async def generate_audio(text, index):
    print(f"[*] Generating audio for chapter {index}...")
    # Strict audio script sanitization
    sanitized_text = re.sub(r"[^a-zA-Z0-9\s.,!?'-]", "", text)
    out_path = os.path.join(DIRS["audio"], f"audio_{index}.mp3")
    try:
        communicate = edge_tts.Communicate(sanitized_text, VOICE, rate="-5%")
        await communicate.save(out_path)
        await asyncio.sleep(2) # Prevent rate-limiting
        return out_path
    except Exception as e:
        print(f"[!] TTS Error for chapter {index}: {e}")
        return None

def run_cmd(cmd):
    """Run a shell command safely and return True on success."""
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def render_manim(code, index):
    print(f"[*] Rendering visuals for chapter {index}...")
    code = validate_and_fix_manim(code, index)
    scene_file = os.path.join(DIRS["scripts"], f"scene_{index}.py")
    visual_output = os.path.join(DIRS["visual"], f"visual_{index}.mp4")

    with open(scene_file, "w") as f:
        f.write(code)

    # Try high quality first using media_dir redirect to avoid local clutter
    cmd = ["manim", "-qh", "--media_dir", DIRS["manim"], scene_file, "GeneratedScene"]
    run_cmd(cmd)

    # Check media_dir output path
    # manim usually puts it in <media_dir>/videos/<script_name>/1080p60/<scene_class>.mp4
    script_base = f"scene_{index}"
    hq_path = os.path.join(DIRS["manim"], "videos", script_base, "1080p60", "GeneratedScene.mp4")

    if os.path.exists(hq_path):
        run_cmd(["cp", hq_path, visual_output])
        return visual_output

    # Fallback to medium quality
    print(f"[!] HQ render failed for ch{index}, trying medium quality...")
    cmd = ["manim", "-qm", "--media_dir", DIRS["manim"], scene_file, "GeneratedScene"]
    run_cmd(cmd)
    mq_path = os.path.join(DIRS["manim"], "videos", script_base, "720p30", "GeneratedScene.mp4")

    if os.path.exists(mq_path):
        run_cmd(["cp", mq_path, visual_output])
        return visual_output

    # If both quality attempts failed, skip this chapter entirely
    print(f"❌ Render completely failed for chapter {index}. Skipping this chapter.")
    print(f"   Check the generated code at: {scene_file}")
    return None

def create_chapter_video(index, visual_path, audio_path):
    """Create chapter video using simple FFmpeg merging logic."""
    chapter_path = os.path.join(DIRS["chunks"], f"ch_{index}.mp4")

    if not visual_path or not os.path.exists(visual_path):
        print(f"[!] Missing visual for chapter {index}")
        return None

    if not audio_path or not os.path.exists(audio_path):
        print(f"[!] Missing audio for chapter {index}")
        return None

    ret = run_cmd([
        "ffmpeg", "-y", "-i", visual_path, "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac", "-shortest", chapter_path,
        "-loglevel", "error"
    ])
    
    if ret and os.path.exists(chapter_path):
        return chapter_path
    return None

def stitch_final(list_file_path):
    print("[*] Stitching final video...")
    master_path = os.path.join(DIRS["final"], "master.mp4")
    
    merged_ok = run_cmd([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file_path,
        "-c:v", "copy", "-c:a", "aac",
        master_path, "-loglevel", "error"
    ])

    if not merged_ok or not os.path.exists(master_path):
        print("❌ Failed to build master.mp4")
        return None

    final_production = os.path.join(DIRS["final"], "final_production.mp4")
    
    if os.path.exists("bg.mp3"):
        print("[*] Mixing background music...")
        # Since we removed wav normalizations, we mix directly (which handles standard mp3s fine)
        run_cmd([
            "ffmpeg", "-y", "-i", master_path, "-stream_loop", "-1", "-i", "bg.mp3",
            "-filter_complex", "[1:a]volume=0.06[a1];[0:a][a1]amix=inputs=2:duration=first[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
            final_production, "-loglevel", "error"
        ])
    else:
        run_cmd(["cp", master_path, final_production])

    # NEW: Create a copy in root directory for vrihi.sh compatibility
    root_output = "final_production.mp4"
    if os.path.exists(final_production):
        print(f"[*] Copying final video to root directory for vrihi.sh...")
        run_cmd(["cp", final_production, root_output])

    return final_production if os.path.exists(final_production) else None

# --- 3. MAIN LOOP ---

def main():
    chapters = get_chapters(TOPIC)
    print(f"\n[+] Chapters planned: {chapters}\n")

    completed = []
    
    for i, title in enumerate(chapters):
        try:
            script, code = get_chapter_content(title, TOPIC)

            audio_path = None
            try:
                audio_path = asyncio.run(generate_audio(script, i))
            except Exception as e:
                print(f"[!] edge-tts failed for chapter {i}: {e}")

            if not audio_path or not os.path.exists(audio_path):
                print(f"[!] Confirmed missing audio file after TTS generation for ch {i}.")
                continue

            visual_path = render_manim(code, i)
            if not visual_path:
                print(f"[!] Rendering failed for ch {i}.")
                continue

            chapter_path = create_chapter_video(i, visual_path, audio_path)
            if chapter_path:
                completed.append(chapter_path)
            else:
                print(f"[!] Merge failed for chapter {i}")
        except Exception as e:
            print(f"[!] Chapter {i} failed with error: {e}")
            continue

    if not completed:
        print("❌ All chapters failed. Exiting.")
        sys.exit(1)

    list_file_path = os.path.join(DIRS["chunks"], "list.txt")
    with open(list_file_path, "w") as f:
        for ch_path in completed:
            # use relative or absolute paths carefully
            f.write(f"file '{os.path.abspath(ch_path)}'\n")

    final_video = stitch_final(list_file_path)

    if final_video and os.path.exists(final_video):
        print(f"\n[+] SUCCESS! Final file ready at: {final_video}")
    else:
        print("\n❌ Failed to generate the final production video.")
        
    print("\n[*] Intermediate files have been preserved in the media/ directories.")

if __name__ == "__main__":
    main()
