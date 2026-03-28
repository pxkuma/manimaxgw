import os
import sys
import json
import asyncio
import subprocess
import re
import urllib.request
import urllib.error
import edge_tts

# --- 1. CONFIGURATION ---
if len(sys.argv) < 2:
    print("❌ Error: You forgot to provide a topic!")
    sys.exit(1)

TOPIC = sys.argv[1]

# Create safe topic name for folders (truncated to prevent OS file path errors)
SAFE_TOPIC = re.sub(r'[^a-zA-Z0-9_\-]', '_', TOPIC.strip()).strip('_')
if not SAFE_TOPIC:
    SAFE_TOPIC = "default_topic"
SAFE_TOPIC = SAFE_TOPIC[:50].strip('_')

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

# Ollama configuration (env vars set by docker-compose or host)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "deepseek-v3.1:671b-cloud")

VOICE = "en-GB-RyanNeural"

def clean_json(text):
    return text.replace('```json', '').replace('```python', '').replace('```', '').strip()

def get_ai_response(prompt):
    print(f"[*] Consulting local Ollama ({MODEL_NAME}). This may take a while...")
    data = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    
    req = urllib.request.Request(
        OLLAMA_URL, 
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        # Deepseek 671b takes extremely long, 30 min timeout
        with urllib.request.urlopen(req, timeout=1800) as response:
            result = json.loads(response.read().decode('utf-8'))
            return clean_json(result.get('response', ''))
    except Exception as e:
        print(f"[!] Ollama connection failed: {e}")
        print("    Ensure Ollama is running, the model name is exactly correct, and 'OLLAMA_HOST=0.0.0.0' is set on your host if inside Docker.")
        sys.exit(1)

# --- 2. PIPELINE FUNCTIONS ---

def get_chapters(topic):
    print(f"[*] (Step 2) Enhancing prompt & planning comprehensive curriculum for: {topic[:50]}...")
    prompt = f"""You are a world-class curriculum designer, educator, and Manim animation director.
The user wants a HIGHLY DETAILED, LONG, comprehensive educational video on this topic: "{topic}"

Your job is to transform this simple topic into a full educational masterpiece. Think like a university professor preparing a lecture series.

REQUIREMENTS:
1. Determine the appropriate number of chapters based on the user's topic. If the topic explicitly asks for a "short", "quick", or "single chapter" video, you MUST generate EXACTLY 1 chapter. Otherwise, break the topic into 3-6 detailed chapters.
2. For EACH chapter, you MUST provide ALL of the following:
   a) A clear title and learning objective
   b) Specific VISUAL PLAN: exact diagram types (flowcharts, layered architectures, comparison tables, step-by-step processes), with color schemes and layout descriptions
   c) REAL-WORLD EXAMPLES and ANALOGIES that make the concept click for a complete beginner (e.g., "think of a stack like a pile of plates")
   d) COORDINATE CONSTRAINTS: specify safe zones, grouping strategies, and ensure NO visual elements overlap
   e) AUDIO NARRATION PLAN: key talking points, timing hints (e.g., "pause here for 2 seconds while diagram builds")
   f) MATHEMATICAL VALUES or DATA POINTS if applicable (exact numbers, formulas, sample calculations)
3. Each chapter should produce a 20-30 second animation segment.
4. If generating multiple chapters, include practical examples/use cases and make the final chapter a summary/recap. If generating a single chapter, incorporate an example and brief conclusion directly into it.

OUTPUT FORMAT - Return EXACTLY a JSON array of strings:
[
  "Chapter 1: [Title]. Learning objective: [what student learns]. Visual plan: [detailed diagram description with colors and layout]. Examples: [real-world analogy]. Audio plan: [narration key points, 10-15 sentences worth]. Constraints: [positioning rules].",
  "Chapter 2: ...",
  ...
]
Return ONLY the JSON array. No markdown, no pre-text, no post-text."""
    
    raw = get_ai_response(prompt)

    # Stage 1: standard parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Stage 2: extract between first [ and last ] then parse
    print(f"[!] Failed to parse JSON plan directly. Attempting extraction...")
    start = raw.find('[')
    end = raw.rfind(']') + 1
    if start != -1 and end > start:
        chunk = raw[start:end]
        try:
            return json.loads(chunk)
        except json.JSONDecodeError:
            pass

    # Stage 3: regex — pull out each "..." entry capturing the full value between
    # the outermost pair of quotes on each array line, even if content is malformed
    print(f"[!] Bracket parse also failed. Using regex line extraction...")
    chapters = []
    # Match items that start with optional whitespace, a quote, content, closing quote+comma/end
    # We greedily capture across possible internal escaped or unescaped quotes using rfind trick per line
    lines = raw.splitlines()
    buffer = ""
    in_item = False
    for line in lines:
        stripped = line.strip()
        if not in_item:
            if stripped.startswith('"'):
                in_item = True
                buffer = stripped
        else:
            buffer += " " + stripped

        if in_item:
            # Check if the buffer closes: ends with ", or "  (last item)
            temp = buffer.rstrip().rstrip(',').rstrip()
            if temp.endswith('"') and len(temp) > 1:
                # Extract from first " to last "
                fs = buffer.index('"')
                ls = buffer.rindex('"')
                if ls > fs:
                    chapters.append(buffer[fs+1:ls])
                    buffer = ""
                    in_item = False

    if chapters:
        return chapters

    raise ValueError(f"Could not parse chapters from AI response. Snippet: {raw[:300]}")

MANIM_PROMPT_TEMPLATE = """
You are an expert Manim (Community Edition v0.18) animator and world-class technical educator.
Create a highly visual, detailed, LONG technical scene for the following chapter curriculum.
This is part of an in-depth educational series — do NOT rush or shorten anything.

TOPIC OVERVIEW: "{topic}"
DETAILED CHAPTER PLAN TO IMPLEMENT:
"{chapter_title}"

STRICT OUTPUT FORMAT — respond with ONLY raw JSON, no markdown, no explanation:
{{
  "audio_script": "Your narration here",
  "manim_code": "<full python code here>"
}}

CRITICAL AUDIO_SCRIPT RULES:
- Write 10-15 clear, educational sentences that explain the concept step by step IN DEPTH
- Start by briefly stating what this chapter covers and why it matters
- Include at least one real-world example or analogy (e.g., "Think of a queue like a line at a coffee shop")
- Walk through each visual element as it appears: "Now, as you can see on screen..."
- End with a brief summary sentence connecting to the next concept
- Act like a confident, passionate teacher — clear, engaging, informative
- STRICTLY plain text narration only — absolutely NO emojis, markdown, bullets, or code formatting
- NO special math symbols, hashtags, or unusual punctuation that breaks TTS
- Use simple punctuation: periods and commas only
- Make it conversational, easy to understand, and thorough

MANIM CODE REQUIREMENTS:
- Class name MUST be: GeneratedScene
- Must start with: from manim import *
- Inherit from Scene
- End with self.wait(3)
- DO NOT artificially shorten the code. This must be a LONG, DETAILED, in-depth animation.
- Create MULTIPLE sub-animations within the scene: build up, transform, highlight, then clean up before the next sub-section
- Use self.play(FadeOut(*self.mobjects)) between sub-sections to create clean transitions
- Target 25-35 seconds of total animation time per scene
- Ensure animations do not overlap based on the specified coordinates in the curriculum
- Create VISUAL DIAGRAMS with shapes, arrows, and labeled components — NOT walls of text
- Include at least 2-3 distinct visual phases (e.g., introduce concept, show example, show comparison)

ABSOLUTE RULES - NO TEXT OVERLAYS:
- DO NOT create title cards or persistent text labels that stay on screen
- DO NOT use corner text or fixed position text overlays
- Text should ONLY be used as small labels inside diagram components (2-3 words max per label)
- All text must be part of animated diagram elements that appear and disappear with the scene flow
- Focus on SHAPES, BOXES, ARROWS, FLOWS — not paragraphs or explanations in text form
- The narration explains the concept — visuals should show structure and relationships

MANDATORY LAYOUT SAFETY AND MANIM RULES (CRITICAL - VIOLATIONS WILL CAUSE CRASHES):
1. FORBIDDEN: FRAME_WIDTH, FRAME_HEIGHT (deprecated) — use config.frame_width and config.frame_height
2. FORBIDDEN: .shift(), .to_edge(), .to_corner(), or manual coordinates like [0,2,0]
3. FORBIDDEN: MoveAlongPath or .point_from_proportion() on a DashedVMobject or VGroup. They have no points and will cause a crash! If you need a path, use a continuous basic Mobject like Circle, Line, or Arc.
4. FORBIDDEN: MathTex and Tex. LaTeX is NOT installed. You MUST use Text() for all text and math. Write equations as simple strings like Text("F = ma") or Text("cos(theta)").
5. FORBIDDEN: Passing a lambda to get_area(). You MUST pass a graph mobject (e.g. axes.plot(lambda x: ...)) to get_area, NOT the lambda directly.
6. MANDATORY LAYOUT PATTERN (follow exactly):
   a) Create all visual elements (boxes, arrows, labels)
   b) Group them: master_group = VGroup(element1, element2, element3, ...)
   c) Arrange vertically: master_group.arrange(DOWN, buff=0.5)
   d) Scale to fit safely: master_group.scale_to_fit_width(config.frame_width - 3)
   e) Center everything: master_group.move_to(ORIGIN)
7. EVERY element must be inside the master_group — no exceptions
8. Keep font_size <= 28 for labels. NEVER use max_width parameter on Text() objects as it is invalid. Use manual newlines if text is too long.
9. Test bounds: all objects must fit in a (config.frame_width - 3) x (config.frame_height - 2) safe zone

VISUAL STYLE:
- BLACK background with color-coded shapes: BLUE_D, TEAL_D, GREEN_D, GOLD_D, RED_D, PURPLE_D, WHITE
- Create structured diagrams: containers, layers, flows, processes, data paths
- Use smooth transitions: DrawBorderThenFill, FadeIn, GrowFromCenter, Create
- Target 25-35 seconds of animation to match narration length
- Brief highlights with SurroundingRectangle to emphasize key parts
- Use LaggedStart for groups of related elements appearing together

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

# Scene transition (use between sub-sections):
self.play(FadeOut(*self.mobjects), run_time=0.5)
self.wait(0.3)

# Safe composition (ALWAYS USE THIS PATTERN):
master_group = VGroup(element1, element2, element3)  # Add ALL scene elements
master_group.arrange(DOWN, buff=0.6)  # Arrange vertically with spacing
master_group.scale_to_fit_width(config.frame_width - 3)  # Safe scaling
master_group.move_to(ORIGIN)  # Center on canvas
self.play(LaggedStart(*[FadeIn(obj) for obj in master_group], lag_ratio=0.3))
self.wait(2)

Now create a COMPLETE GeneratedScene for "{chapter_title}" (topic: "{topic}"):
- Write thorough educational narration (10-15 sentences with examples)
- Build MULTIPLE visual phases (introduce, example, comparison/summary)
- Use the safe composition pattern to keep everything in bounds
- Include real-world analogies in the narration
- NO title cards, NO text overlays, NO walls of text
- Make it clean, visual, perfectly centered, and LONG enough to teach properly
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
    
    # Strip hallucinated max_width parameter
    code = re.sub(r',\s*max_width=[0-9.]+', '', code)
    code = re.sub(r'max_width=[0-9.]+\s*,?\s*', '', code)
    
    # Auto-fix get_area(lambda...) to get_area(axes.plot(lambda...))
    # This specifically catches common hallucination of passing lambda directly to axes.get_area
    code = re.sub(r'get_area\(\s*lambda\s+([^:]+):([^,]+),', r'get_area(axes.plot(lambda \1: \2),', code)

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
