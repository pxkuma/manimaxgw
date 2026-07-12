"""
renderer_api.py — FastAPI wrapper around auto_video.py
Exposes POST /generate  → streams stdout/stderr as Server-Sent Events
Exposes GET  /health    → simple health check
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

app = FastAPI(title="Manimax Renderer", version="1.0.0")

# ── paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
SCRIPT     = os.path.join(BASE_DIR, "auto_video.py")
MEDIA_DIR  = os.getenv("MEDIA_DIR", "/media")          # shared volume mount
PYTHON_CMD = sys.executable                             # same python that runs uvicorn


# ── request/response models ────────────────────────────────────────────────────
class GenerateRequest(BaseModel):
    topic:           str          = Field(..., min_length=1, max_length=200)
    num_chapters:    int          = Field(3,  ge=1, le=10)
    target_duration: int          = Field(180, ge=10)
    render_quality:  str          = Field("high")
    target_fps:      int          = Field(60,  ge=1)
    learner_level:   str          = Field("intermediate")
    teaching_style:  str          = Field("conceptual")
    visual_style:    str          = Field("balanced")
    auth_token:      str | None   = None


# ── health ─────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "renderer": "ready"}


# ── generate (SSE stream) ───────────────────────────────────────────────────────
@app.post("/generate")
async def generate(req: GenerateRequest, request: Request):
    """
    Runs auto_video.py as a subprocess and streams every line of output
    as Server-Sent Events so the web service can relay them to Socket.io.

    SSE format:
        data: <json-encoded line>\n\n
    """
    env = {**os.environ}
    env["PYTHONUNBUFFERED"]              = "1"
    env["MEDIA_DIR"]                     = MEDIA_DIR
    env["MANIMAX_NUM_CHAPTERS"]            = str(req.num_chapters)
    env["MANIMAX_TARGET_DURATION"]         = str(req.target_duration)
    env["MANIMAX_RENDER_QUALITY"]          = req.render_quality
    env["MANIMAX_TARGET_FPS"]              = str(req.target_fps)
    env["MANIMAX_ALLOW_LOW_QUALITY_FALLBACK"] = "1"
    env["MANIMAX_SYNC_TOLERANCE"]          = env.get("MANIMAX_SYNC_TOLERANCE", "0.2")
    env["MANIMAX_MIN_SCENE_SECONDS"]       = env.get("MANIMAX_MIN_SCENE_SECONDS", "4.0")
    env["MANIMAX_MAX_STATIC_HOLD_SECONDS"] = env.get("MANIMAX_MAX_STATIC_HOLD_SECONDS", "1.5")
    env["MANIMAX_MIN_UNIQUE_SCENE_TYPES"]  = env.get("MANIMAX_MIN_UNIQUE_SCENE_TYPES", "4")
    env["IS_DOCKER"]                     = "true"

    cmd = [PYTHON_CMD, SCRIPT, req.topic]

    async def event_stream() -> AsyncIterator[str]:
        import json as _json
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=BASE_DIR,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,   # merge stderr into stdout
        )

        try:
            assert proc.stdout is not None
            while True:
                # Check if the HTTP client disconnected
                if await request.is_disconnected():
                    proc.terminate()
                    break

                try:
                    line = await asyncio.wait_for(proc.stdout.readline(), timeout=1.0)
                except asyncio.TimeoutError:
                    # Send a keepalive comment so the connection stays open
                    yield ": keepalive\n\n"
                    continue

                if not line:
                    break

                text = line.decode(errors="replace").rstrip("\n")
                yield f"data: {_json.dumps({'text': text})}\n\n"

            await proc.wait()
            exit_code = proc.returncode
            yield f"data: {_json.dumps({'exit_code': exit_code, 'done': True})}\n\n"

        except asyncio.CancelledError:
            proc.terminate()
            raise

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
