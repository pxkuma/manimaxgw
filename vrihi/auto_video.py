#!/usr/bin/env python3
"""
Vrihi - AI Teaching Video Generator (v4)
Pipeline: PLAN (GPT-5) -> CODE DRAFT (Qwen3) -> CODE REFINE (DeepSeek)
- Proper JSON parsing (no fragile find/rfind hacks)
- Teaching-first narration (actually explains concepts)
- Manim code grounded in a plan, not improvised
"""

import os, sys, json, asyncio, glob, shutil, subprocess, re, time
import urllib.request, urllib.error
import edge_tts

# --- STDOUT ------------------------------------------------------------------
os.environ['PYTHONUNBUFFERED'] = '1'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

def _uni():
    try:
        'OK'.encode(sys.stdout.encoding or 'utf-8'); return True
    except Exception:
        return False
U = _uni()

ICONS = {
    "info":     "[i]",
    "success":  "[+]",
    "error":    "[!]",
    "progress": "[*]",
    "step":     "[>]",
    "chapter":  "[#]",
    "audio":    "[A]",
    "video":    "[V]",
    "render":   "[R]",
    "plan":     "[P]",
}

def log(msg, level="info"):
    prefix = ICONS.get(level, "[-]")
    try:
        print(f"{prefix} {msg}", flush=True)
    except UnicodeEncodeError:
        print(f"{ICONS.get(level,'[-]')} {msg.encode('ascii','replace').decode()}", flush=True)

# --- CLI ---------------------------------------------------------------------
if len(sys.argv) < 2:
    log("Usage: python auto_video.py 'Your Topic' [duration_in_seconds]", "error"); sys.exit(1)
TOPIC = sys.argv[1]
try:
    USER_DURATION = int(sys.argv[2]) if len(sys.argv) > 2 else None
except (ValueError, IndexError):
    USER_DURATION = None

# --- ENV HELPERS -------------------------------------------------------------
def _int(name, default, lo=None, hi=None):
    try: v = int(os.getenv(name, str(default)))
    except Exception: v = default
    if lo is not None: v = max(lo, v)
    if hi is not None: v = min(hi, v)
    return v

def _float(name, default, lo=None, hi=None):
    try: v = float(os.getenv(name, str(default)))
    except Exception: v = default
    if lo is not None: v = max(lo, v)
    if hi is not None: v = min(hi, v)
    return v

def load_dotenv():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(p): return
    with open(p) as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
load_dotenv()

# --- CONFIG ------------------------------------------------------------------
TARGET_DURATION   = USER_DURATION or _int("VRIHI_TARGET_DURATION",  45, lo=10)
NUM_CHAPTERS      = _int("VRIHI_NUM_CHAPTERS",       3, lo=1, hi=10)
CHAPTER_DURATION  = TARGET_DURATION // max(1, NUM_CHAPTERS)
RENDER_QUALITY    = os.getenv("VRIHI_RENDER_QUALITY", "high").strip().lower()
TARGET_FPS        = _int("VRIHI_TARGET_FPS", 60, lo=1)
SYNC_TOLERANCE    = _float("VRIHI_SYNC_TOLERANCE", 0.2, lo=0.0)
ALLOW_LQ_FALLBACK = os.getenv("VRIHI_ALLOW_LOW_QUALITY_FALLBACK","1").lower() in {"1","true","yes"}
TTS_VOICE         = os.getenv("VRIHI_TTS_VOICE", "en-GB-RyanNeural")

OLLAMA_URL        = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
QWEN_MODEL        = os.getenv("QWEN_MODEL", "qwen3-coder:480b-cloud")
DEEPSEEK_MODEL    = os.getenv("DEEPSEEK_MODEL", "deepseek-v3.2:cloud")
GITHUB_TOKEN      = os.getenv("GITHUB_TOKEN", "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")
GPT5_URL          = os.getenv("GPT5_URL", "https://models.inference.ai.azure.com/chat/completions")

AI_MAX_RETRIES    = _int("VRIHI_AI_MAX_RETRIES", 2, lo=0)
AI_RETRY_DELAY    = _float("VRIHI_AI_RETRY_DELAY_SECONDS", 3.0, lo=0)
AI_BACKOFF        = _int("VRIHI_AI_TIMEOUT_BACKOFF_SECONDS", 30, lo=0)

SAFE_TOPIC = re.sub(r'[^a-zA-Z0-9_\-]', '_', TOPIC.strip()).strip('_')[:50] or "video"
DIRS = {k: f"media/{k}/{SAFE_TOPIC}" for k in
        ("scripts","audio","visual","chunks","final","manim")}
for d in DIRS.values(): os.makedirs(d, exist_ok=True)

log(f"Topic     : {TOPIC}", "info")
log(f"Duration  : {TARGET_DURATION}s total | {NUM_CHAPTERS} chapters | ~{CHAPTER_DURATION}s each", "info")
log(f"Planning  : GPT-5 (via Github token)", "info")
log(f"Code Gen  : {QWEN_MODEL} -> {DEEPSEEK_MODEL}", "info")
log(f"Render    : {RENDER_QUALITY} @ {TARGET_FPS}fps", "info")

# --- AI LAYER ----------------------------------------------------------------

def call_gpt5(prompt, timeout=180):
    token = GITHUB_TOKEN.strip() if GITHUB_TOKEN else ""
    if token == "PLACE_GITHUB_TOKEN_HERE" or not token:
        log("GITHUB_TOKEN not set. Please set it or replace 'PLACE_GITHUB_TOKEN_HERE'.", "error")
    
    data = json.dumps({
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are an expert AI teaching video planner."},
            {"role": "user", "content": prompt}
        ]
    }).encode()
    req = urllib.request.Request(
        GPT5_URL, data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    )
    for attempt in range(AI_MAX_RETRIES + 1):
        log(f"GPT-5 [planning] attempt {attempt+1}...", "progress")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.loads(r.read().decode())
                raw = resp["choices"][0]["message"]["content"]
                if raw and raw.strip():
                    log("AI responded (GPT-5)", "success")
                    return raw.strip()
            raise ValueError("Empty response")
        except urllib.error.HTTPError as e:
            if attempt < AI_MAX_RETRIES:
                time.sleep(AI_RETRY_DELAY * (attempt+1))
            else:
                log(f"GPT-5 HTTP {e.code}: {e.read().decode()}", "error")
        except Exception as e:
            if attempt < AI_MAX_RETRIES:
                time.sleep(AI_RETRY_DELAY * (attempt+1))
            else:
                log(f"GPT-5 failed: {e}", "error")
    return None

def ollama_ai(prompt, model, label="", timeout=180):
    for attempt in range(AI_MAX_RETRIES + 1):
        t = timeout + attempt * AI_BACKOFF
        log(f"{model} [{label}] attempt {attempt+1}...", "progress")
        try:
            data = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
            req  = urllib.request.Request(
                OLLAMA_URL, data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=t) as r:
                raw = json.loads(r.read().decode()).get("response","")
                if raw and raw.strip():
                    log(f"AI responded ({model})", "success")
                    return raw.strip()
            raise ValueError("Empty response")
        except urllib.error.HTTPError as e:
            log(f"{model} failed: HTTP Error {e.code}: {e.reason}", "error")
            if 400 <= e.code < 500:
                log(f"  Client error (HTTP {e.code}) — not retrying. Check model name or Ollama auth.", "error")
                break  # no point retrying 4xx
            if attempt < AI_MAX_RETRIES:
                time.sleep(AI_RETRY_DELAY * (attempt+1))
        except Exception as e:
            if attempt < AI_MAX_RETRIES:
                time.sleep(AI_RETRY_DELAY * (attempt+1))
            else:
                log(f"{model} failed: {e}", "error")
    return None

# --- SAFE JSON PARSER --------------------------------------------------------
def _strip_fence(text):
    text = text.strip()
    text = re.sub(r'^```[a-zA-Z]*\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()

def parse_json(text):
    if not text: return None
    text = _strip_fence(text)
    try: return json.loads(text)
    except json.JSONDecodeError: pass
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch in ('{', '['):
            try:
                obj, _ = decoder.raw_decode(text, i)
                return obj
            except json.JSONDecodeError:
                continue
    log(f"parse_json: no valid JSON found.", "error")
    return None

# --- STAGE 1: GPT-5 PLANNING -------------------------------------------------

PLANNING_PROMPT = """\
You are designing a structured teaching video on: "{topic}"

The total duration is {duration} seconds, broken into {n} chapters.
Your job is to produce a complete workplan defining all chapters, animation concepts, and the exact audio script for each.

Respond with ONLY a raw JSON array of objects. No markdown, no explanation. Exact schema for the array elements:
[
  {{
    "chapter_title": "Short title",
    "core_concept": "One sentence explaining the main idea",
    "teaching_points": ["point 1", "point 2"],
    "visual_metaphor": "Specific description of what should be drawn/animated using Manim.",
    "key_terms": ["term1"],
    "script": "The exact spoken narration text for this chapter. Target around {words_per_chapter} words. Start explaining immediately without intro filler."
  }}
]
"""

def get_full_plan():
    log("Planning full video structure with GPT-5...", "step")
    words = int(CHAPTER_DURATION * 2.5)
    prompt = PLANNING_PROMPT.format(topic=TOPIC, duration=TARGET_DURATION, n=NUM_CHAPTERS, words_per_chapter=words)
    raw = call_gpt5(prompt, timeout=120)
    result = parse_json(raw) if raw else None
    if isinstance(result, list) and result:
        return result
    log("GPT-5 planning failed.", "error")
    return None

# --- STAGE 2: MANIM CODE GENERATION (QWEN3) ----------------------------------

MANIM_PROMPT = """\
You are an expert Manim (Community Edition v0.18) animator writing a cinematic educational animation.

TOPIC: "{topic}"
CHAPTER: "{chapter}"
DURATION: ~{duration} seconds

TEACHING PLAN:
- Core concept: {core_concept}
- Visual metaphor to animate: {visual_metaphor}
- Key terms: {key_terms}
- Teaching points: {teaching_points}

NARRATION SCRIPT (animate visuals timed to this):
{script}

OUTPUT FORMAT:
Respond with ONLY a raw JSON object containing the code. No markdown fences.
{{
  "manim_code": "<complete python code as a single escaped string>"
}}

REQUIREMENTS:
- Class MUST be exactly: GeneratedScene
- Inherit from Scene. Start construct() with: self.camera.background_color = "#0d1117"
- End with: self.wait(3)
- Use colors: BLUE_D, TEAL_D, GREEN_D, GOLD_D, RED_D, PURPLE_D, WHITE, GRAY_B
- Minimum buff=0.35 between elements. Maximum 11 units wide (use .scale(0.8) if needed).
- Always include title card at start.
Write COMPLETE, RUNNABLE Python code.
"""

def get_manim_code(plan):
    chapter = plan.get("chapter_title", "Chapter")
    log(f"Generating initial Manim code (Qwen3): {chapter}...", "render")
    prompt = MANIM_PROMPT.format(
        topic=TOPIC, chapter=chapter, duration=CHAPTER_DURATION,
        core_concept=plan.get("core_concept",""),
        visual_metaphor=plan.get("visual_metaphor",""),
        key_terms=", ".join(plan.get("key_terms",[])),
        teaching_points="; ".join(plan.get("teaching_points",[])),
        script=plan.get("script","")
    )
    raw = ollama_ai(prompt, QWEN_MODEL, label="manim-gen", timeout=300)
    if not raw: return None
    result = parse_json(raw)
    if isinstance(result, dict) and result.get("manim_code"):
        return result["manim_code"]
    if raw and "class GeneratedScene" in raw:
        return _strip_fence(raw)
    return None

# --- STAGE 3: CODE REFINEMENT (DEEPSEEK V3.1) --------------------------------

REVIEW_PROMPT = """\
You are an expert Manim (Community CE v0.18) developer. 
Review the following generated Manim code for the chapter "{chapter}".
Improve the code structure, ensure all elements fit on screen (16:9, width ~13, height ~7), fix any animation overlap, and enhance the visual reasoning based on this core concept: {core_concept}

NARRATION SCRIPT:
{script}

ORIGINAL CODE:
{code}

Respond with ONLY a raw JSON object containing the refined code. No markdown.
{{
  "manim_code": "<complete refined python code as a single escaped string>"
}}
"""

def refine_manim_code(plan, code):
    chapter = plan.get("chapter_title", "Chapter")
    log(f"Refining Manim code (DeepSeek): {chapter}...", "render")
    prompt = REVIEW_PROMPT.format(
        chapter=chapter,
        core_concept=plan.get("core_concept",""),
        script=plan.get("script",""),
        code=code
    )
    raw = ollama_ai(prompt, DEEPSEEK_MODEL, label="manim-refine", timeout=300)
    if not raw: return code
    result = parse_json(raw)
    if isinstance(result, dict) and result.get("manim_code"):
        return result["manim_code"]
    if raw and "class GeneratedScene" in raw:
        return _strip_fence(raw)
    return code

# --- MANIM VALIDATOR ---------------------------------------------------------

def fix_manim(code, chapter):
    if not code: return None
    if "class GeneratedScene" not in code:
        code = re.sub(r"class \w+\s*\(Scene\)\s*:", "class GeneratedScene(Scene):", code, count=1)
    if "from manim import" not in code:
        code = "from manim import *\n" + code
    if "background_color" not in code:
        code = code.replace(
            "def construct(self):",
            'def construct(self):\n        self.camera.background_color = "#0d1117"', 1
        )
    if "self.wait" not in code:
        code = code.rstrip() + "\n        self.wait(3)\n"
    return code

# --- TTS ---------------------------------------------------------------------

async def gen_audio(script, index):
    log(f"Generating voice ch{index+1}...", "audio")
    out = os.path.join(DIRS["audio"], f"audio_{index}.mp3")
    clean = re.sub(r'[^\w\s.,!?\'-]', '', script)
    voices = [TTS_VOICE, "en-US-AriaNeural", "en-US-GuyNeural", "en-GB-SoniaNeural"]
    for v in voices:
        try:
            await edge_tts.Communicate(clean, v, rate="-5%").save(out)
            if os.path.exists(out) and os.path.getsize(out) > 0:
                log(f"Voice OK ({v})", "success"); return out
        except Exception as e:
            log(f"TTS {v} failed: {e}", "error")
    return None

# --- RENDER ------------------------------------------------------------------

def get_duration(path):
    try:
        r = subprocess.run(
            ["ffprobe","-v","error","-show_entries","format=duration",
             "-of","default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception: return 0.0

def find_render(script_name):
    pat = os.path.join(DIRS["manim"], "videos", script_name, "**", "GeneratedScene.mp4")
    hits = glob.glob(pat, recursive=True)
    return max(hits, key=os.path.getmtime) if hits else None

def render_manim(code, index):
    log(f"Rendering ch{index+1}...", "render")
    scene_file  = os.path.join(DIRS["scripts"], f"scene_{index}.py")
    output_path = os.path.join(DIRS["visual"],  f"visual_{index}.mp4")
    sname       = f"scene_{index}"

    with open(scene_file, "w") as f: f.write(code)

    vdir = os.path.join(DIRS["manim"], "videos", sname)
    if os.path.exists(vdir): shutil.rmtree(vdir, ignore_errors=True)

    # Resolve manim binary.
    # Priority: Docker image venv (/opt/venv) when IS_DOCKER=true,
    # otherwise local .venv — but only if its shebang interpreter exists on this
    # machine (the host .venv shebang points to the host Python path which is
    # unreachable inside the container).
    def _manim_usable(path):
        if not os.path.isfile(path):
            return False
        try:
            with open(path, "rb") as _f:
                first = _f.readline().decode(errors="replace").strip()
            if first.startswith("#!"):
                interp = first[2:].split()[0]
                return os.path.isfile(interp)  # shebang interpreter must exist here
            return True  # no shebang → assume usable
        except Exception:
            return False

    _script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.getenv("IS_DOCKER", "").lower() in ("1", "true", "yes"):
        _candidates = ["/opt/venv/bin/manim",
                       os.path.join(_script_dir, ".venv", "bin", "manim")]
    else:
        _candidates = [os.path.join(_script_dir, ".venv", "bin", "manim"),
                       "/opt/venv/bin/manim"]
    manim_cmd = next((c for c in _candidates if _manim_usable(c)), "manim")

    q_map = {"low":["-ql"],"medium":["-qm"],"high":["-qh"],"ultra":["-qk"]}
    sel   = RENDER_QUALITY if RENDER_QUALITY in q_map else "high"
    attempts = q_map[sel][:]
    if ALLOW_LQ_FALLBACK and sel not in ("low","medium"):
        if "-qm" not in attempts: attempts.append("-qm")
        if "-ql" not in attempts: attempts.append("-ql")

    fps_map = {"-qk": max(60,TARGET_FPS), "-qh": TARGET_FPS,
               "-qm": min(TARGET_FPS,30),  "-ql": min(TARGET_FPS,15)}

    for qf in attempts:
        fps = fps_map.get(qf, TARGET_FPS)
        cmd = [manim_cmd, qf, "--fps", str(fps),
               "--media_dir", DIRS["manim"], scene_file, "GeneratedScene"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        vpath = find_render(sname)
        if r.returncode == 0 and vpath:
            shutil.copy2(vpath, output_path)
            log(f"Rendered {qf} @ {fps}fps", "success")
            return output_path
        if r.stderr:
            log(f"Manim error ({qf}): {r.stderr[-400:]}", "error")

    log("All render attempts failed — inserting placeholder.", "error")
    dur = max(10, CHAPTER_DURATION)
    subprocess.run([
        "ffmpeg","-y",
        "-f","lavfi","-i",f"color=c=black:s=1920x1080:d={dur}",
        "-f","lavfi","-i","anullsrc=r=44100:cl=stereo",
        "-c:v","libx264","-c:a","aac","-shortest",
        output_path,"-loglevel","error"
    ])
    return output_path if os.path.exists(output_path) else None

def merge_chapter(index, video, audio):
    log(f"Merging ch{index+1}...", "video")
    if not video or not audio or not os.path.exists(video) or not os.path.exists(audio):
        return None
    out  = os.path.join(DIRS["chunks"], f"ch_{index}.mp4")
    adur = get_duration(audio)
    vdur = get_duration(video)
    log(f"  Audio {adur:.1f}s  Video {vdur:.1f}s", "info")
    if adur <= 0 or vdur <= 0: return None

    cmd = ["ffmpeg","-y","-i",video,"-i",audio]
    if vdur + SYNC_TOLERANCE < adur:
        pad = adur - vdur + 0.15
        cmd.extend(["-vf", f"tpad=stop_mode=clone:stop_duration={pad:.2f}"])
    cmd.extend([
        "-map","0:v:0","-map","1:a:0",
        "-c:v","libx264","-preset","slow","-crf","18",
        "-c:a","aac","-b:a","160k",
        "-t",f"{adur:.2f}","-movflags","+faststart",
        out,"-loglevel","error"
    ])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0 and os.path.exists(out):
        log(f"  Chapter ready: {get_duration(out):.1f}s", "success")
        return out
    log(f"  Merge failed: {r.stderr[:200]}", "error")
    return None

def finalize(chunks):
    log("Stitching final video...", "video")
    lf     = os.path.join(DIRS["chunks"], "concat.txt")
    master = os.path.join(DIRS["final"],  "master.mp4")
    final  = os.path.join(DIRS["final"],  "final_production.mp4")

    with open(lf,"w") as f:
        for c in chunks: f.write(f"file '{os.path.abspath(c)}'\n")

    r = subprocess.run([
        "ffmpeg","-y","-f","concat","-safe","0","-i",lf,
        "-c:v","libx264","-preset","fast","-c:a","aac",
        "-movflags","+faststart", master, "-loglevel","error"
    ], capture_output=True, text=True)
    if r.returncode != 0:
        log("Concat failed", "error"); return None

    if os.path.exists("bg.mp3"):
        log("Mixing background music...", "audio")
        subprocess.run([
            "ffmpeg","-y","-i",master,"-stream_loop","-1","-i","bg.mp3",
            "-filter_complex","[1:a]volume=0.06[bg];[0:a][bg]amix=inputs=2:duration=first[a]",
            "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac",
            final,"-loglevel","error"
        ], capture_output=True)
    else:
        shutil.copy2(master, final)

    if os.path.exists(final):
        shutil.copy2(final, "final_production.mp4")
        return final
    return None

# --- MAIN --------------------------------------------------------------------

def main():
    print("\n" + "="*54)
    log("Vrihi Teaching Video Generator (GPT-5 + Qwen + DeepSeek)", "video")
    log(f"Topic    : {TOPIC}", "info")
    log(f"Duration : {TARGET_DURATION}s | {NUM_CHAPTERS} chapters | ~{CHAPTER_DURATION}s each", "info")
    print("="*54 + "\n")

    full_plan = get_full_plan()
    if not full_plan:
        log("Fatal: GPT-5 planning failed.", "error"); sys.exit(1)
    
    n_chapters = len(full_plan)
    log(f"GPT-5 created {n_chapters} chapters.", "success")

    completed = []

    for i, plan in enumerate(full_plan):
        chapter = plan.get("chapter_title", f"Chapter {i+1}")
        script = plan.get("script", "")
        print(f"\n{'- '*18}\nChapter {i+1}/{n_chapters}: {chapter}")

        try:
            log(f"  Core : {plan.get('core_concept','')}", "info")
            if not script:
                log("Skipping — missing script.", "error"); continue
            log(f"  Script ({len(script.split())} words): {script[:80]}...", "info")

            # Qwen3 Coder generates draft
            draft_code = get_manim_code(plan)
            if not draft_code:
                log("Skipping — Manim draft generation failed.", "error"); continue
            
            # DeepSeek V3.1 refines
            refined_code = refine_manim_code(plan, draft_code)
            
            # Fix basics
            final_code = fix_manim(refined_code, chapter)
            if not final_code:
                log("Skipping — Manim fix failed.", "error"); continue

            # Audio
            audio = asyncio.run(gen_audio(script, i))
            if not audio:
                log("Skipping — audio failed.", "error"); continue

            # Render
            video = render_manim(final_code, i)
            if not video:
                log("Skipping — render failed.", "error"); continue

            # Merge
            chunk = merge_chapter(i, video, audio)
            if chunk:
                completed.append(chunk)
                log(f"Chapter {i+1} complete!", "success")

        except Exception as e:
            log(f"Chapter {i+1} crashed: {e}", "error")
            import traceback; traceback.print_exc()

    print(f"\n{'='*54}")
    if not completed:
        log("All chapters failed.", "error"); sys.exit(1)

    log(f"Completed {len(completed)}/{n_chapters} chapters", "info")
    final = finalize(completed)

    if final:
        dur = get_duration(final)
        print(f"\n{'='*54}")
        log(f"SUCCESS! {dur:.1f}s video ready", "success")
        log(f"Path : {final}", "info")
        log(f"Also : ./final_production.mp4", "info")
        print("="*54 + "\n")
    else:
        log("Finalization failed.", "error"); sys.exit(1)

if __name__ == "__main__":
    main()
