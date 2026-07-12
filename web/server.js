const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const path = require('path');
const fs = require('fs');

const app = express();
const server = http.createServer(app);
const io = new Server(server);

const PORT = process.env.FRONTEND_PORT || process.env.PORT || 3020;

// ── Renderer service URL (internal Docker network) ──────────────────────────
const RENDERER_URL = process.env.RENDERER_URL || 'http://renderer:5050';

// ── Media directory (shared volume) ─────────────────────────────────────────
// In Docker the shared volume is mounted at /media; locally fall back to ./renderer/media
const MEDIA_DIR = process.env.MEDIA_DIR || path.join(__dirname, '..', 'renderer', 'media');
const SCRIPTS_ROOT = path.join(MEDIA_DIR, 'scripts');

function resolveWithin(baseDir, ...segments) {
    const resolvedBase   = path.resolve(baseDir);
    const resolvedTarget = path.resolve(baseDir, ...segments);
    const baseWithSep    = `${resolvedBase}${path.sep}`;
    if (!resolvedTarget.startsWith(baseWithSep)) return null;
    return resolvedTarget;
}

// ── Rate-limiting / concurrency helpers ─────────────────────────────────────
function parsePositiveInt(value, fallback) {
    const parsed = Number.parseInt(String(value), 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

const MAX_CONCURRENT_GENERATIONS = parsePositiveInt(process.env.MANIMAX_MAX_CONCURRENT_GENERATIONS || '2', 2);
const MIN_GENERATE_INTERVAL_MS   = parsePositiveInt(process.env.MANIMAX_MIN_GENERATE_INTERVAL_MS || '8000', 8000);
const REQUIRED_GENERATE_TOKEN    = String(process.env.MANIMAX_GENERATE_TOKEN || '').trim();

// ── Static serving ───────────────────────────────────────────────────────────
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Serve generated media files from the shared volume
app.use('/media', express.static(MEDIA_DIR));

// ── REST: list projects ──────────────────────────────────────────────────────
app.get('/api/projects', (req, res) => {
    const finalDir = path.join(MEDIA_DIR, 'final');
    try {
        const projects = fs.readdirSync(finalDir)
            .filter(f => fs.statSync(path.join(finalDir, f)).isDirectory())
            .map(name => {
                const projectPath = path.join(finalDir, name);
                const finalVideo  = path.join(projectPath, 'final_production.mp4');
                const scriptsDir  = path.join(MEDIA_DIR, 'scripts', name);
                const chunksDir   = path.join(MEDIA_DIR, 'chunks',  name);

                let chapters = [];
                if (fs.existsSync(scriptsDir)) {
                    chapters = fs.readdirSync(scriptsDir)
                        .filter(f => f.startsWith('scene_') && f.endsWith('.py'))
                        .sort((a, b) => {
                            const numA = parseInt(a.match(/\d+/)?.[0] || 0);
                            const numB = parseInt(b.match(/\d+/)?.[0] || 0);
                            return numA - numB;
                        })
                        .map(f => {
                            const idx          = f.match(/\d+/)?.[0] || '0';
                            const chapterVideo = path.join(chunksDir, `ch_${idx}.mp4`);
                            return {
                                index:      parseInt(idx),
                                scriptFile: f,
                                hasVideo:   fs.existsSync(chapterVideo),
                                videoPath:  `/media/chunks/${name}/ch_${idx}.mp4`,
                                scriptPath: `/media/scripts/${name}/${f}`,
                            };
                        });
                }

                return {
                    name,
                    hasVideo:  fs.existsSync(finalVideo),
                    videoPath: `/media/final/${name}/final_production.mp4`,
                    chapters,
                    createdAt: fs.statSync(projectPath).mtime,
                };
            })
            .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

        res.json(projects);
    } catch (_) {
        res.json([]);
    }
});

// ── REST: get script content ─────────────────────────────────────────────────
app.get('/api/script/:project/:file', (req, res) => {
    const { project, file } = req.params;
    if (!/^[A-Za-z0-9_-]+$/.test(project) || !/^[A-Za-z0-9_.-]+\.py$/.test(file)) {
        return res.status(400).json({ error: 'Invalid script path' });
    }

    const scriptPath = resolveWithin(SCRIPTS_ROOT, project, file);
    if (!scriptPath) return res.status(400).json({ error: 'Invalid script path' });

    if (fs.existsSync(scriptPath) && fs.statSync(scriptPath).isFile()) {
        res.json({ content: fs.readFileSync(scriptPath, 'utf8') });
    } else {
        res.status(404).json({ error: 'Script not found' });
    }
});

// ── Socket.io ────────────────────────────────────────────────────────────────
const activeGenerations = new Map();      // socket.id → AbortController
const recentGenerateByIp = new Map();

const allowedLearnerLevels   = new Set(['beginner', 'intermediate', 'advanced']);
const allowedTeachingStyles  = new Set(['conceptual', 'story-based', 'exam-focused', 'intuitive']);
const allowedVisualStyles    = new Set(['balanced', 'diagram-heavy', 'equation-heavy', 'minimal']);

function sanitizeChoice(value, allowedSet, fallback) {
    const normalized = String(value || '').trim().toLowerCase();
    return allowedSet.has(normalized) ? normalized : fallback;
}

function normalizeTopic(value) {
    return String(value || '')
        .replace(/[\u0000-\u001F\u007F]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

function durationPreset(duration) {
    switch (duration) {
        case 'quick':  return { num_chapters: 1, target_duration: 45  };
        case 'short':  return { num_chapters: 2, target_duration: 90  };
        case 'medium': return { num_chapters: 4, target_duration: 240 };
        case 'long':   return { num_chapters: 6, target_duration: 480 };
        default:       return { num_chapters: 3, target_duration: 180 };
    }
}

io.on('connection', (socket) => {
    console.log('Client connected:', socket.id);

    // ── generate ──────────────────────────────────────────────────────────────
    socket.on('generate', async (data) => {
        const { topic, mode, duration, learnerLevel, teachingStyle, visualStyle, authToken } = data;

        if (REQUIRED_GENERATE_TOKEN && String(authToken || '').trim() !== REQUIRED_GENERATE_TOKEN) {
            socket.emit('error', { message: 'Unauthorized generation request.' });
            return;
        }
        if (activeGenerations.has(socket.id)) {
            socket.emit('error', { message: 'A generation is already running for this session.' });
            return;
        }
        if (activeGenerations.size >= Math.max(1, MAX_CONCURRENT_GENERATIONS)) {
            socket.emit('error', { message: 'Server is busy. Please wait and retry.' });
            return;
        }

        const clientIp  = socket.handshake.address || socket.conn?.remoteAddress || 'unknown';
        const now       = Date.now();
        const lastAttempt = recentGenerateByIp.get(clientIp) || 0;
        if (now - lastAttempt < Math.max(1000, MIN_GENERATE_INTERVAL_MS)) {
            socket.emit('error', { message: 'Please wait a few seconds before starting another generation.' });
            return;
        }
        recentGenerateByIp.set(clientIp, now);
        if (recentGenerateByIp.size > 2000) {
            for (const [ip, ts] of recentGenerateByIp.entries()) {
                if (now - ts > 10 * 60 * 1000) recentGenerateByIp.delete(ip);
            }
        }

        const normalizedTopic = normalizeTopic(topic);
        if (!normalizedTopic) {
            socket.emit('error', { message: 'Topic cannot be empty' }); return;
        }
        if (normalizedTopic.length > 180) {
            socket.emit('error', { message: 'Topic is too long. Keep it under 180 characters.' }); return;
        }

        socket.emit('status', { message: 'Starting generation...', phase: 'init' });

        const preset = durationPreset(duration);
        const body   = JSON.stringify({
            topic:           normalizedTopic,
            num_chapters:    preset.num_chapters,
            target_duration: preset.target_duration,
            render_quality:  'high',
            target_fps:      60,
            learner_level:   sanitizeChoice(learnerLevel,   allowedLearnerLevels,  'intermediate'),
            teaching_style:  sanitizeChoice(teachingStyle,  allowedTeachingStyles, 'conceptual'),
            visual_style:    sanitizeChoice(visualStyle,    allowedVisualStyles,   'balanced'),
        });

        const controller = new AbortController();
        activeGenerations.set(socket.id, controller);

        try {
            // ── call renderer service ──────────────────────────────────────
            const rendererRes = await fetch(`${RENDERER_URL}/generate`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body,
                signal: controller.signal,
            });

            if (!rendererRes.ok) {
                const errText = await rendererRes.text().catch(() => 'unknown error');
                socket.emit('error', { message: `Renderer error ${rendererRes.status}: ${errText}` });
                activeGenerations.delete(socket.id);
                return;
            }

            // ── stream SSE from renderer → Socket.io ──────────────────────
            const reader = rendererRes.body.getReader();
            const dec    = new TextDecoder();
            let buf      = '';
            let exitCode = null;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buf += dec.decode(value, { stream: true });
                const lines = buf.split('\n');
                buf = lines.pop(); // keep incomplete line

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    let payload;
                    try { payload = JSON.parse(line.slice(6)); } catch (_) { continue; }

                    if (payload.done) {
                        exitCode = payload.exit_code;
                        continue;
                    }

                    const text = payload.text || '';

                    // Parse progress from log lines (same logic as before)
                    if (text.includes('Writing narration') || text.includes('Calling AI')) {
                        socket.emit('status', { message: 'Planning content...',     phase: 'planning',   progress: 15 });
                    } else if (text.includes('Planning visuals') || text.includes('Generating illustration plan') ||
                               (text.includes('Generated') && text.includes('illustration scenes'))) {
                        socket.emit('status', { message: 'Designing visuals...',    phase: 'generating', progress: 30 });
                    } else if (text.includes('Generating voice') || text.includes('Voice generated')) {
                        socket.emit('status', { message: 'Creating voice...',       phase: 'audio',      progress: 50 });
                    } else if (text.includes('Rendering animation') || text.includes('Building animation')) {
                        socket.emit('status', { message: 'Rendering animation...',  phase: 'rendering',  progress: 70 });
                    } else if (text.includes('Stitching') || text.includes('Merging')) {
                        socket.emit('status', { message: 'Finalizing video...',     phase: 'stitching',  progress: 90 });
                    } else if (text.includes('SUCCESS')) {
                        socket.emit('status', { message: 'Complete!', phase: 'complete', progress: 100 });
                    }

                    socket.emit('log', { text });
                }
            }

            activeGenerations.delete(socket.id);

            if (exitCode === 0) {
                const safeTopic = normalizedTopic
                    .replace(/[^a-zA-Z0-9_\-]/g, '_')
                    .substring(0, 50)
                    .replace(/_+$/, '');
                socket.emit('complete', { success: true, project: safeTopic, message: 'Video generated successfully!' });
            } else {
                socket.emit('complete', { success: false, message: 'Generation failed. Check logs for details.' });
            }

        } catch (err) {
            activeGenerations.delete(socket.id);
            if (err.name === 'AbortError') {
                socket.emit('status', { message: 'Cancelled', phase: 'cancelled' });
            } else {
                console.error('Renderer fetch error:', err);
                socket.emit('error', { message: `Could not reach renderer: ${err.message}` });
            }
        }
    });

    // ── cancel ────────────────────────────────────────────────────────────────
    socket.on('cancel', () => {
        const ctrl = activeGenerations.get(socket.id);
        if (ctrl) {
            ctrl.abort();
            activeGenerations.delete(socket.id);
            socket.emit('status', { message: 'Cancelled', phase: 'cancelled' });
        }
    });

    // ── disconnect ────────────────────────────────────────────────────────────
    socket.on('disconnect', () => {
        console.log('Client disconnected:', socket.id);
        const ctrl = activeGenerations.get(socket.id);
        if (ctrl) {
            ctrl.abort();
            activeGenerations.delete(socket.id);
        }
    });
});

// ── Start server ─────────────────────────────────────────────────────────────
server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
        console.error(`\n  ✗ Port ${PORT} is already in use.`);
        console.error(`    Set a different port with: FRONTEND_PORT=<port>\n`);
        process.exit(1);
    }
    throw err;
});

server.listen(PORT, () => {
    console.log(`\n  ███╗   ███╗ █████╗ ███╗   ██╗██╗███╗   ███╗ █████╗ ██╗  ██╗`);
    console.log(`  ████╗ ████║██╔══██╗████╗  ██║██║████╗ ████║██╔══██╗╚██╗██╔╝`);
    console.log(`  ██╔████╔██║███████║██╔██╗ ██║██║██╔████╔██║███████║ ╚███╔╝ `);
    console.log(`  ██║╚██╔╝██║██╔══██║██║╚██╗██║██║██║╚██╔╝██║██╔══██║ ██╔██╗ `);
    console.log(`  ██║ ╚═╝ ██║██║  ██║██║ ╚████║██║██║ ╚═╝ ██║██║  ██║██╔╝ ██╗`);
    console.log(`  ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝`);
    console.log(`\n  🎬 Manimax Web  →  http://localhost:${PORT}`);
    console.log(`  🔗 Renderer     →  ${RENDERER_URL}\n`);
});
