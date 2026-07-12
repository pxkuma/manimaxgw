 const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const app = express();
const server = http.createServer(app);
const io = new Server(server);

const PORT = process.env.FRONTEND_PORT || process.env.PORT || 3020;
const ROOT_DIR = path.join(__dirname, '..', 'vrihi');
const SCRIPTS_ROOT = path.resolve(ROOT_DIR, 'media', 'scripts');

function resolveWithin(baseDir, ...segments) {
    const resolvedBase = path.resolve(baseDir);
    const resolvedTarget = path.resolve(baseDir, ...segments);
    const baseWithSep = `${resolvedBase}${path.sep}`;

    if (!resolvedTarget.startsWith(baseWithSep)) {
        return null;
    }

    return resolvedTarget;
}

// In Docker: use system python, otherwise use venv
const IS_DOCKER = process.env.IS_DOCKER === 'true' || fs.existsSync('/.dockerenv');
const VENV_PYTHON = path.join(ROOT_DIR, '.venv', 'bin', 'python');
const PYTHON_PATH = IS_DOCKER ? 'python3' : (fs.existsSync(VENV_PYTHON) ? VENV_PYTHON : 'python3');

// Load .env from vrihi directory
const envPath = path.join(ROOT_DIR, '.env');
if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf8');
    envContent.split('\n').forEach(line => {
        const [key, ...valueParts] = line.split('=');
        if (key && valueParts.length > 0) {
            const value = valueParts.join('=').trim();
            if (!process.env[key.trim()]) {
                process.env[key.trim()] = value;
            }
        }
    });
    console.log('Loaded environment from:', envPath);
}

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
app.use('/media', express.static(path.join(ROOT_DIR, 'media')));
app.use('/videos', express.static(path.join(ROOT_DIR, '..', 'Videos', 'production')));

// Get all generated projects
app.get('/api/projects', (req, res) => {
    const finalDir = path.join(ROOT_DIR, 'media', 'final');
    try {
        const projects = fs.readdirSync(finalDir)
            .filter(f => fs.statSync(path.join(finalDir, f)).isDirectory())
            .map(name => {
                const projectPath = path.join(finalDir, name);
                const finalVideo = path.join(projectPath, 'final_production.mp4');
                const scriptsDir = path.join(ROOT_DIR, 'media', 'scripts', name);
                const chunksDir = path.join(ROOT_DIR, 'media', 'chunks', name);
                
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
                            const idx = f.match(/\d+/)?.[0] || '0';
                            const chapterVideo = path.join(chunksDir, `ch_${idx}.mp4`);
                            return {
                                index: parseInt(idx),
                                scriptFile: f,
                                hasVideo: fs.existsSync(chapterVideo),
                                videoPath: `/media/chunks/${name}/ch_${idx}.mp4`,
                                scriptPath: `/media/scripts/${name}/${f}`
                            };
                        });
                }
                
                return {
                    name,
                    hasVideo: fs.existsSync(finalVideo),
                    videoPath: `/media/final/${name}/final_production.mp4`,
                    chapters,
                    createdAt: fs.statSync(projectPath).mtime
                };
            })
            .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
        
        res.json(projects);
    } catch (err) {
        res.json([]);
    }
});

// Get script content
app.get('/api/script/:project/:file', (req, res) => {
    const { project, file } = req.params;
    if (!/^[A-Za-z0-9_-]+$/.test(project) || !/^[A-Za-z0-9_.-]+\.py$/.test(file)) {
        return res.status(400).json({ error: 'Invalid script path' });
    }

    const scriptPath = resolveWithin(SCRIPTS_ROOT, project, file);

    if (!scriptPath) {
        return res.status(400).json({ error: 'Invalid script path' });
    }
    
    if (fs.existsSync(scriptPath) && fs.statSync(scriptPath).isFile()) {
        const content = fs.readFileSync(scriptPath, 'utf8');
        res.json({ content });
    } else {
        res.status(404).json({ error: 'Script not found' });
    }
});

// Active generation processes
const activeProcesses = new Map();
const recentGenerateByIp = new Map();

function parsePositiveInt(value, fallback) {
    const parsed = Number.parseInt(String(value), 10);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

const MAX_CONCURRENT_GENERATIONS = parsePositiveInt(process.env.VRIHI_MAX_CONCURRENT_GENERATIONS || '2', 2);
const MIN_GENERATE_INTERVAL_MS = parsePositiveInt(process.env.VRIHI_MIN_GENERATE_INTERVAL_MS || '8000', 8000);
const REQUIRED_GENERATE_TOKEN = String(process.env.VRIHI_GENERATE_TOKEN || '').trim();

// Socket.io for real-time updates
io.on('connection', (socket) => {
    console.log('Client connected:', socket.id);

    const allowedLearnerLevels = new Set(['beginner', 'intermediate', 'advanced']);
    const allowedTeachingStyles = new Set(['conceptual', 'story-based', 'exam-focused', 'intuitive']);
    const allowedVisualStyles = new Set(['balanced', 'diagram-heavy', 'equation-heavy', 'minimal']);

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
    
    socket.on('generate', (data) => {
        const { topic, mode, duration, learnerLevel, teachingStyle, visualStyle, authToken } = data;

        if (REQUIRED_GENERATE_TOKEN && String(authToken || '').trim() !== REQUIRED_GENERATE_TOKEN) {
            socket.emit('error', { message: 'Unauthorized generation request.' });
            return;
        }

        if (activeProcesses.has(socket.id)) {
            socket.emit('error', { message: 'A generation is already running for this session.' });
            return;
        }

        if (activeProcesses.size >= Math.max(1, MAX_CONCURRENT_GENERATIONS)) {
            socket.emit('error', { message: 'Server is busy. Please wait and retry.' });
            return;
        }

        const clientIp = socket.handshake.address || socket.conn?.remoteAddress || 'unknown';
        const now = Date.now();
        const lastAttempt = recentGenerateByIp.get(clientIp) || 0;
        if (now - lastAttempt < Math.max(1000, MIN_GENERATE_INTERVAL_MS)) {
            socket.emit('error', { message: 'Please wait a few seconds before starting another generation.' });
            return;
        }
        recentGenerateByIp.set(clientIp, now);
        if (recentGenerateByIp.size > 2000) {
            for (const [ip, ts] of recentGenerateByIp.entries()) {
                if (now - ts > 10 * 60 * 1000) {
                    recentGenerateByIp.delete(ip);
                }
            }
        }

        const normalizedTopic = normalizeTopic(topic);
        if (!normalizedTopic) {
            socket.emit('error', { message: 'Topic cannot be empty' });
            return;
        }

        if (normalizedTopic.length > 180) {
            socket.emit('error', { message: 'Topic is too long. Keep it under 180 characters.' });
            return;
        }
        
        socket.emit('status', { message: 'Starting generation...', phase: 'init' });
        
        // Set environment variables based on duration
        const env = { ...process.env };
        
        switch (duration) {
            case 'quick':
                env.VRIHI_NUM_CHAPTERS = '1';
                env.VRIHI_TARGET_DURATION = '45';
                break;
            case 'short':
                env.VRIHI_NUM_CHAPTERS = '2';
                env.VRIHI_TARGET_DURATION = '90';
                break;
            case 'medium':
                env.VRIHI_NUM_CHAPTERS = '4';
                env.VRIHI_TARGET_DURATION = '240';
                break;
            case 'long':
                env.VRIHI_NUM_CHAPTERS = '6';
                env.VRIHI_TARGET_DURATION = '480';
                break;
            default:
                env.VRIHI_NUM_CHAPTERS = '3';
                env.VRIHI_TARGET_DURATION = '180';
        }

        // Quality-first defaults for educational output (respect existing env overrides)
        env.VRIHI_RENDER_QUALITY = env.VRIHI_RENDER_QUALITY || 'high';
        env.VRIHI_TARGET_FPS = env.VRIHI_TARGET_FPS || '60';
        env.VRIHI_ALLOW_LOW_QUALITY_FALLBACK = env.VRIHI_ALLOW_LOW_QUALITY_FALLBACK || '1';
        env.VRIHI_SYNC_TOLERANCE = env.VRIHI_SYNC_TOLERANCE || '0.2';
        env.VRIHI_MIN_SCENE_SECONDS = env.VRIHI_MIN_SCENE_SECONDS || '4.0';
        env.VRIHI_MAX_STATIC_HOLD_SECONDS = env.VRIHI_MAX_STATIC_HOLD_SECONDS || '1.5';
        env.VRIHI_MIN_UNIQUE_SCENE_TYPES = env.VRIHI_MIN_UNIQUE_SCENE_TYPES || '4';

        const scriptPath = path.join(ROOT_DIR, 'auto_video.py');
        // If PYTHON_PATH is a plain command name (no path separator), use it directly.
        // If it's an absolute path (venv), verify it exists before using it.
        const pythonCmd = PYTHON_PATH.includes(path.sep)
            ? (fs.existsSync(PYTHON_PATH) ? PYTHON_PATH : 'python3')
            : PYTHON_PATH;
        console.log(`Using Python: ${pythonCmd}`);
        console.log(`Running: ${pythonCmd} ${scriptPath} "${normalizedTopic}"`);
        
        const proc = spawn(pythonCmd, [scriptPath, normalizedTopic], {
            cwd: ROOT_DIR,
            env
        });
        
        activeProcesses.set(socket.id, proc);
        
        let outputBuffer = '';
        
        proc.stdout.on('data', (data) => {
            const text = data.toString();
            outputBuffer += text;
            
            // Parse progress based on new log format
            if (text.includes('Writing narration') || text.includes('Calling AI')) {
                socket.emit('status', { message: 'Planning content...', phase: 'planning', progress: 15 });
            } else if (
                text.includes('Planning visuals') ||
                text.includes('Generating illustration plan') ||
                (text.includes('Generated') && text.includes('illustration scenes'))
            ) {
                socket.emit('status', { message: 'Designing visuals...', phase: 'generating', progress: 30 });
            } else if (text.includes('Generating voice') || text.includes('Voice generated')) {
                socket.emit('status', { message: 'Creating voice...', phase: 'audio', progress: 50 });
            } else if (text.includes('Rendering animation') || text.includes('Building animation')) {
                socket.emit('status', { message: 'Rendering animation...', phase: 'rendering', progress: 70 });
            } else if (text.includes('Stitching') || text.includes('Merging')) {
                socket.emit('status', { message: 'Finalizing video...', phase: 'stitching', progress: 90 });
            } else if (text.includes('SUCCESS')) {
                socket.emit('status', { message: 'Complete!', phase: 'complete', progress: 100 });
            }
            
            // Send log immediately for real-time updates
            socket.emit('log', { text });
        });
        
        proc.stderr.on('data', (data) => {
            socket.emit('log', { text: data.toString(), type: 'error' });
        });
        
        proc.on('close', (code) => {
            activeProcesses.delete(socket.id);
            
            if (code === 0) {
                // Get the project name from the topic
                const safeTopic = normalizedTopic.replace(/[^a-zA-Z0-9_\-]/g, '_').substring(0, 50).replace(/_+$/, '');
                
                socket.emit('complete', {
                    success: true,
                    project: safeTopic,
                    message: 'Video generated successfully!'
                });
            } else {
                socket.emit('complete', {
                    success: false,
                    message: 'Generation failed. Check logs for details.'
                });
            }
        });
        
        proc.on('error', (err) => {
            socket.emit('error', { message: `Process error: ${err.message}` });
            activeProcesses.delete(socket.id);
        });
    });
    
    socket.on('cancel', () => {
        const proc = activeProcesses.get(socket.id);
        if (proc) {
            proc.kill('SIGTERM');
            activeProcesses.delete(socket.id);
            socket.emit('status', { message: 'Cancelled', phase: 'cancelled' });
        }
    });
    
    socket.on('disconnect', () => {
        console.log('Client disconnected:', socket.id);
        const proc = activeProcesses.get(socket.id);
        if (proc) {
            proc.kill('SIGTERM');
            activeProcesses.delete(socket.id);
        }
    });
});

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
    console.log(`\n  🎬 Manimax Server running at http://localhost:${PORT}\n`);
});
