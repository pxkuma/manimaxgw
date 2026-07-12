// Manimax - Modern AI Video Studio
class Manimax {
    constructor() {
        this.socket = io();
        this.currentProject = null;
        this.currentChapter = null;
        this.projects = [];
        this.isGenerating = false;
        this.selectedDuration = 'short';
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.setupSocket();
        this.loadProjects();
    }
    
    get elements() {
        return {
            // Navigation
            navBtns: document.querySelectorAll('.nav-btn'),
            views: document.querySelectorAll('.view'),
            
            // Generate View
            topicInput: document.getElementById('topicInput'),
            learnerLevelInput: document.getElementById('learnerLevelInput'),
            teachingStyleInput: document.getElementById('teachingStyleInput'),
            visualStyleInput: document.getElementById('visualStyleInput'),
            generateBtn: document.getElementById('generateBtn'),
            durationCards: document.querySelectorAll('.duration-card'),
            previewIdle: document.getElementById('previewIdle'),
            previewProgress: document.getElementById('previewProgress'),
            progressTopic: document.getElementById('progressTopic'),
            progressRing: document.getElementById('progressRing'),
            progressPercent: document.getElementById('progressPercent'),
            steps: document.querySelectorAll('.step'),
            terminalBody: document.getElementById('terminalBody'),
            terminalToggle: document.getElementById('terminalToggle'),
            cancelBtn: document.getElementById('cancelBtn'),
            
            // Archive View
            projectList: document.getElementById('projectList'),
            refreshBtn: document.getElementById('refreshBtn'),
            chaptersSection: document.getElementById('chaptersSection'),
            chaptersList: document.getElementById('chaptersList'),
            emptyState: document.getElementById('emptyState'),
            viewerSection: document.getElementById('viewerSection'),
            videoTitle: document.getElementById('videoTitle'),
            viewerBadge: document.getElementById('viewerBadge'),
            videoPlayer: document.getElementById('videoPlayer'),
            downloadBtn: document.getElementById('downloadBtn'),
            codeContent: document.getElementById('codeContent'),
            copyCodeBtn: document.getElementById('copyCodeBtn'),
            viewFullBtn: document.getElementById('viewFullBtn'),
            
            // Status
            connectionStatus: document.getElementById('connectionStatus'),
        };
    }
    
    bindEvents() {
        const el = this.elements;
        
        // Navigation
        el.navBtns.forEach(btn => {
            btn.addEventListener('click', () => this.switchView(btn.dataset.view));
        });
        
        // Generate
        el.generateBtn.addEventListener('click', () => this.startGeneration());
        el.topicInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.startGeneration();
        });
        
        // Duration selection
        el.durationCards.forEach(card => {
            card.addEventListener('click', () => {
                el.durationCards.forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                this.selectedDuration = card.dataset.duration;
            });
        });
        
        // Terminal toggle
        el.terminalToggle?.addEventListener('click', () => {
            const container = el.terminalToggle.closest('.terminal-container');
            container.classList.toggle('collapsed');
            el.terminalToggle.textContent = container.classList.contains('collapsed') ? '[+]' : '[-]';
        });
        
        // Cancel generation
        el.cancelBtn?.addEventListener('click', () => this.cancelGeneration());
        
        // Library
        el.refreshBtn?.addEventListener('click', () => this.loadProjects());
        el.copyCodeBtn?.addEventListener('click', () => this.copyCode());
        el.downloadBtn?.addEventListener('click', () => this.downloadVideo());
        el.viewFullBtn?.addEventListener('click', () => this.viewFullVideo());
    }
    
    setupSocket() {
        const el = this.elements;
        const statusDot = el.connectionStatus?.querySelector('.status-dot');
        const statusText = el.connectionStatus?.querySelector('.status-text');
        
        this.socket.on('connect', () => {
            if (statusDot) statusDot.classList.remove('disconnected');
            if (statusText) statusText.textContent = 'Online';
        });
        
        this.socket.on('disconnect', () => {
            if (statusDot) statusDot.classList.add('disconnected');
            if (statusText) statusText.textContent = 'Offline';
        });
        
        this.socket.on('status', (data) => {
            this.updateProgress(data);
        });
        
        this.socket.on('log', (data) => {
            this.appendLog(data.text, data.type);
        });
        
        this.socket.on('complete', (data) => {
            this.handleComplete(data);
        });
        
        this.socket.on('error', (data) => {
            this.showError(data.message);
        });
    }
    
    switchView(view) {
        const el = this.elements;
        
        el.navBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.view === view);
        });
        
        el.views.forEach(v => {
            v.classList.toggle('active', v.id === `${view}View`);
        });
        
        if (view === 'library') {
            this.loadProjects();
        }
    }
    
    startGeneration() {
        const el = this.elements;
        const topic = el.topicInput.value.trim();
        
        if (!topic) {
            this.shakeInput();
            return;
        }
        
        if (this.isGenerating) return;
        
        this.isGenerating = true;
        el.generateBtn.classList.add('loading');
        el.generateBtn.disabled = true;
        
        // Reset cancel button text
        if (el.cancelBtn) el.cancelBtn.textContent = 'Cancel';
        
        // Switch to progress view
        el.previewIdle?.classList.add('hidden');
        el.previewProgress?.classList.remove('hidden');
        el.progressTopic.textContent = topic;
        el.terminalBody.innerHTML = '';
        
        // Reset progress
        this.updateProgress({ progress: 0, phase: 'init' });
        
        this.socket.emit('generate', {
            topic,
            duration: this.selectedDuration,
            mode: 'full',
            authToken: window.localStorage.getItem('vrihiGenerateToken') || ''
        });
    }
    
    cancelGeneration() {
        this.socket.emit('cancel');
        this.resetGenerateUI();
    }
    
    updateProgress(data) {
        const el = this.elements;
        
        if (data.progress !== undefined) {
            const percent = Math.round(data.progress);
            const circumference = 2 * Math.PI * 54; // r = 54
            const offset = circumference - (percent / 100) * circumference;
            
            if (el.progressRing) {
                el.progressRing.style.strokeDashoffset = offset;
            }
            if (el.progressPercent) {
                el.progressPercent.textContent = `${percent}%`;
            }
        }
        
        if (data.phase) {
            const phaseOrder = ['planning', 'generating', 'audio', 'rendering', 'stitching'];
            const currentIdx = phaseOrder.indexOf(data.phase);
            
            el.steps.forEach(step => {
                const stepPhase = step.dataset.phase;
                const stepIdx = phaseOrder.indexOf(stepPhase);
                step.classList.remove('active', 'completed');
                
                if (stepIdx < currentIdx) {
                    step.classList.add('completed');
                } else if (stepIdx === currentIdx) {
                    step.classList.add('active');
                }
            });
        }
    }
    
    appendLog(text, type = '') {
        const el = this.elements;
        if (!el.terminalBody) return;
        
        const line = document.createElement('div');
        line.className = `log-line ${type}`;
        line.textContent = text;
        el.terminalBody.appendChild(line);
        el.terminalBody.scrollTop = el.terminalBody.scrollHeight;
    }
    
    handleComplete(data) {
        if (data.success) {
            this.updateProgress({ progress: 100, phase: 'complete' });
            this.appendLog('✓ Video generated successfully!', 'success');
            
            setTimeout(() => {
                this.resetGenerateUI();
                if (this.elements.topicInput) {
                    this.elements.topicInput.value = '';
                }
                this.switchView('library');
                this.loadProjects().then(() => {
                    if (data.project) {
                        const proj = this.projects.find(p => p.name === data.project);
                        if (proj) this.selectProject(proj);
                    }
                });
            }, 1500);
        } else {
            this.isGenerating = false;
            const el = this.elements;
            if (el.generateBtn) {
                el.generateBtn.classList.remove('loading');
                el.generateBtn.disabled = false;
            }
            this.appendLog('✗ Generation failed. Check logs above.', 'error');
            if (el.cancelBtn) {
                el.cancelBtn.textContent = 'Go Back';
            }
        }
    }
    
    resetGenerateUI() {
        const el = this.elements;
        this.isGenerating = false;
        el.generateBtn?.classList.remove('loading');
        if (el.generateBtn) el.generateBtn.disabled = false;
        
        // Reset to idle view
        el.previewIdle?.classList.remove('hidden');
        el.previewProgress?.classList.add('hidden');
    }
    
    shakeInput() {
        const el = this.elements;
        el.topicInput.style.animation = 'none';
        el.topicInput.offsetHeight;
        el.topicInput.style.animation = 'shake 0.4s ease';
    }
    
    showError(message) {
        this.appendLog(`Error: ${message}`, 'error');
    }
    
    async loadProjects() {
        const el = this.elements;
        if (!el.projectList) return;
        
        el.projectList.innerHTML = '<div class="loading-spinner"></div>';
        
        try {
            const res = await fetch('/api/projects');
            this.projects = await res.json();
            this.renderProjectList();
        } catch (err) {
            el.projectList.innerHTML = '<p style="padding: 20px; color: var(--text-tertiary);">Failed to load projects</p>';
        }
    }
    
    renderProjectList() {
        const el = this.elements;
        
        if (this.projects.length === 0) {
            el.projectList.innerHTML = '<p style="padding: 20px; color: var(--text-tertiary); text-align: center;">No projects yet</p>';
            return;
        }
        
        el.projectList.innerHTML = this.projects.map((proj, idx) => `
            <div class="project-item ${this.currentProject?.name === proj.name ? 'active' : ''}" data-index="${idx}">
                <div class="project-name">${this.escapeHtml(this.formatProjectName(proj.name))}</div>
                <div class="project-meta">
                    <span class="project-chapters">${proj.chapters.length} chapters</span>
                    <span>${proj.hasVideo ? '✓' : '...'}</span>
                </div>
            </div>
        `).join('');
        
        el.projectList.querySelectorAll('.project-item').forEach(item => {
            item.addEventListener('click', () => {
                const projIdx = parseInt(item.dataset.index, 10);
                const proj = Number.isInteger(projIdx) ? this.projects[projIdx] : null;
                if (proj) this.selectProject(proj);
            });
        });
    }
    
    selectProject(project) {
        const el = this.elements;
        
        this.currentProject = project;
        this.currentChapter = null;
        
        // Update project list active state
        el.projectList.querySelectorAll('.project-item').forEach(item => {
            const projIdx = parseInt(item.dataset.index, 10);
            const match = Number.isInteger(projIdx) && this.projects[projIdx]?.name === project.name;
            item.classList.toggle('active', match);
        });
        
        // Show chapters section
        el.chaptersSection?.classList.remove('hidden');
        
        // Show viewer, hide empty state
        el.emptyState?.classList.add('hidden');
        el.viewerSection?.classList.remove('hidden');
        
        // Update title and badge
        if (el.videoTitle) el.videoTitle.textContent = this.formatProjectName(project.name);
        if (el.viewerBadge) el.viewerBadge.textContent = 'Full Video';
        
        this.loadFullVideo(project);
        this.renderChapters(project);
    }
    
    loadFullVideo(project) {
        const el = this.elements;
        
        if (project.hasVideo && el.videoPlayer) {
            el.videoPlayer.src = project.videoPath;
            el.videoPlayer.load();
        }
        
        el.viewFullBtn?.classList.add('active');
        
        // Load first chapter code by default
        if (project.chapters.length > 0) {
            this.loadChapterCode(project.chapters[0]);
        } else {
            if (el.codeContent) el.codeContent.textContent = '// No chapters available';
        }
    }
    
    renderChapters(project) {
        const el = this.elements;
        if (!el.chaptersList) return;
        
        if (project.chapters.length === 0) {
            el.chaptersList.innerHTML = '<p class="no-chapters">No chapters available</p>';
            return;
        }
        
        el.chaptersList.innerHTML = project.chapters.map(ch => `
            <div class="chapter-item ${this.currentChapter?.index === ch.index ? 'active' : ''}" data-index="${ch.index}">
                <div class="chapter-num">${ch.index + 1}</div>
                <div class="chapter-details">
                    <span class="chapter-name">Chapter ${ch.index + 1}</span>
                    <span class="chapter-status ${ch.hasVideo ? 'ready' : ''}">${ch.hasVideo ? '● Ready' : '○ Processing'}</span>
                </div>
            </div>
        `).join('');
        
        el.chaptersList.querySelectorAll('.chapter-item').forEach(item => {
            item.addEventListener('click', () => {
                const ch = project.chapters.find(c => c.index === parseInt(item.dataset.index));
                if (ch) this.selectChapter(ch);
            });
        });
    }
    
    selectChapter(chapter) {
        const el = this.elements;
        
        // Toggle off if clicking same chapter
        if (this.currentChapter?.index === chapter.index) {
            this.viewFullVideo();
            return;
        }
        
        this.currentChapter = chapter;
        
        // Update UI states
        el.viewFullBtn?.classList.remove('active');
        el.chaptersList?.querySelectorAll('.chapter-item').forEach(item => {
            item.classList.toggle('active', parseInt(item.dataset.index) === chapter.index);
        });
        
        // Update badge
        if (el.viewerBadge) el.viewerBadge.textContent = `Chapter ${chapter.index + 1}`;
        
        // Load chapter video
        if (chapter.hasVideo && el.videoPlayer) {
            el.videoPlayer.src = chapter.videoPath;
            el.videoPlayer.load();
        }
        
        this.loadChapterCode(chapter);
    }
    
    viewFullVideo() {
        const el = this.elements;
        
        if (!this.currentProject) return;
        
        this.currentChapter = null;
        el.viewFullBtn?.classList.add('active');
        el.chaptersList?.querySelectorAll('.chapter-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Update badge
        if (el.viewerBadge) el.viewerBadge.textContent = 'Full Video';
        
        if (this.currentProject.hasVideo && el.videoPlayer) {
            el.videoPlayer.src = this.currentProject.videoPath;
            el.videoPlayer.load();
        }
    }
    
    async loadChapterCode(chapter) {
        const el = this.elements;
        if (!el.codeContent) return;
        
        try {
            const res = await fetch(`/api/script/${encodeURIComponent(this.currentProject.name)}/${encodeURIComponent(chapter.scriptFile)}`);
            const data = await res.json();
            el.codeContent.textContent = data.content || '# Code not available';
        } catch (err) {
            el.codeContent.textContent = '# Failed to load code';
        }
    }
    
    async copyCode() {
        const el = this.elements;
        const code = el.codeContent?.textContent;
        if (!code) return;
        
        try {
            await navigator.clipboard.writeText(code);
            const btn = el.copyCodeBtn;
            const original = btn.innerHTML;
            btn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="20,6 9,17 4,12"/>
                </svg>
                Copied!
            `;
            setTimeout(() => { btn.innerHTML = original; }, 2000);
        } catch (err) {
            console.error('Copy failed:', err);
        }
    }
    
    downloadVideo() {
        const el = this.elements;
        const videoSrc = el.videoPlayer?.src;
        if (!videoSrc) return;
        
        const a = document.createElement('a');
        a.href = videoSrc;
        a.download = this.currentChapter 
            ? `chapter_${this.currentChapter.index + 1}.mp4`
            : `${this.currentProject.name}.mp4`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }
    
    formatProjectName(name) {
        return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    }

    escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    window.manimax = new Manimax();
});

// Add shake animation
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        20%, 60% { transform: translateX(-8px); }
        40%, 80% { transform: translateX(8px); }
    }
`;
document.head.appendChild(style);
