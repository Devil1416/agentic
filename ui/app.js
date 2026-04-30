// ╔══════════════════════════════════════════════════════════╗
// ║  Reflexion — Created by Harsh Ashar                        ║
// ║  github.com/doriangraypng                                    ║
// ║  Unauthorized reproduction is noticed.                   ║
// ╚══════════════════════════════════════════════════════════╝
﻿/**
 * app.js â€” Client-side logic for Reflexion Web UI v2.
 *
 * Features: SSE streaming, multi-session, artifact display, code copy, file explorer.
 */

// Auto-detect API base: if served from the backend, use same origin; otherwise fallback
const API = window.location.protocol === 'file:'

// ─── fingerprint ────────────────────────────────────────────
const _PROVENANCE = {
    author: "Harsh Ashar",
    github: "github.com/doriangraypng",
    project: "Reflexion",
    integrity: "e05cc90ace7e",
};
// ─── /fingerprint ───────────────────────────────────────────

    ? 'http://localhost:8000'
    : window.location.origin;

// â”€â”€â”€ DOM Elements â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const chatContainer = document.getElementById('chat-container');
const chatMessages  = document.getElementById('chat-messages');
const chatInput     = document.getElementById('chat-input');
const sendBtn       = document.getElementById('send-btn');
const welcomeScreen = document.getElementById('welcome-screen');
const fileTree      = document.getElementById('file-tree');
const statusDot     = document.getElementById('status-dot');
const codeViewer    = document.getElementById('code-viewer');
const codeViewerTitle = document.getElementById('code-viewer-title');
const codeViewerPre = document.getElementById('code-viewer-pre');
const toastContainer = document.getElementById('toast-container');
const sessionList   = document.getElementById('session-list');

const btnThink      = document.getElementById('btn-think');
const btnAuto       = document.getElementById('btn-auto');

let isStreaming = false;
let thinkingMode = false;
let autoExecute = false;
let currentSessionId = null;
let messageHistoryLength = 0;
let pollInterval = null;

// â”€â”€â”€ Init â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
document.addEventListener('DOMContentLoaded', () => {
    checkConnection();
    loadSessionState();
    loadSessions();
    loadHistory();
    loadFiles();

    chatInput.addEventListener('input', autoResize);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);

    document.getElementById('toggle-sidebar').addEventListener('click', () => {
        document.getElementById('app').classList.toggle('sidebar-collapsed');
    });

    document.querySelectorAll('.welcome-prompt').forEach(btn => {
        btn.addEventListener('click', () => {
            chatInput.value = btn.dataset.prompt;
            sendMessage();
        });
    });

    document.getElementById('btn-refresh-files').addEventListener('click', loadFiles);
    document.getElementById('btn-run-task').addEventListener('click', runTask);
    document.getElementById('btn-session-info').addEventListener('click', showSessionInfo);
    document.getElementById('btn-reset').addEventListener('click', newSession);
    document.getElementById('btn-models').addEventListener('click', showModels);
    document.getElementById('btn-new-session').addEventListener('click', newSession);
    document.getElementById('code-viewer-close').addEventListener('click', () => {
        codeViewer.classList.remove('open');
    });

    // Toggles
    btnThink.addEventListener('click', () => {
        thinkingMode = !thinkingMode;
        btnThink.classList.toggle('active', thinkingMode);
        btnThink.title = `Thinking Mode: ${thinkingMode ? 'ON' : 'OFF'}`;
        btnThink.style.color = thinkingMode ? 'var(--accent-violet)' : 'inherit';
        btnThink.style.borderColor = thinkingMode ? 'var(--accent-violet)' : 'var(--border-color)';
        // Send command silently to backend
        fetch(`${API}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: thinkingMode ? '/think_on' : '/think_off' })
        });
        showToast(`Thinking Mode ${thinkingMode ? 'Enabled' : 'Disabled'}`);
    });

    btnAuto.addEventListener('click', () => {
        autoExecute = !autoExecute;
        btnAuto.classList.toggle('active', autoExecute);
        btnAuto.title = `Auto-Execute: ${autoExecute ? 'ON' : 'OFF'}`;
        btnAuto.style.color = autoExecute ? 'var(--accent-cyan)' : 'inherit';
        btnAuto.style.borderColor = autoExecute ? 'var(--accent-cyan)' : 'var(--border-color)';
        // Send command silently
        fetch(`${API}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: autoExecute ? '/auto_on' : '/auto_off' })
        });
        showToast(`Auto-Execute ${autoExecute ? 'Enabled' : 'Disabled'}`);
    });

    // Execution Polling
    pollInterval = setInterval(pollHistory, 2000);
    setInterval(loadFiles, 10000);
});

async function pollHistory() {
    if (isStreaming) return; // Don't poll while actively receiving SSE chat
    await loadHistory();
}

async function loadSessionState() {
    try {
        const res = await fetch(`${API}/session`);
        const data = await res.json();
        thinkingMode = !!data.thinking_mode;
        autoExecute = !!data.auto_execute;

        btnThink.classList.toggle('active', thinkingMode);
        btnThink.title = `Thinking Mode: ${thinkingMode ? 'ON' : 'OFF'}`;
        btnThink.style.color = thinkingMode ? 'var(--accent-violet)' : 'inherit';
        btnThink.style.borderColor = thinkingMode ? 'var(--accent-violet)' : 'var(--border-color)';

        btnAuto.classList.toggle('active', autoExecute);
        btnAuto.title = `Auto-Execute: ${autoExecute ? 'ON' : 'OFF'}`;
        btnAuto.style.color = autoExecute ? 'var(--accent-cyan)' : 'inherit';
        btnAuto.style.borderColor = autoExecute ? 'var(--accent-cyan)' : 'var(--border-color)';
    } catch { /* backend not up */ }
}

// â”€â”€â”€ Connection Check â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async function checkConnection() {
    try {
        const res = await fetch(`${API}/`);
        const data = await res.json();
        statusDot.classList.remove('disconnected');
        statusDot.title = `Connected â€” ${data.models} models`;
        currentSessionId = data.session_id;
    } catch {
        statusDot.classList.add('disconnected');
        statusDot.title = 'Disconnected â€” start backend with: python backend/server.py';
        showToast('Backend not reachable. Run: python backend/server.py', 'error');
    }
}

// â”€â”€â”€ Sessions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async function loadSessions() {
    try {
        const res = await fetch(`${API}/sessions`);
        const data = await res.json();
        currentSessionId = data.current_session_id;
        renderSessionList(data.sessions, data.current_session_id);
    } catch { /* backend not up */ }
}

function renderSessionList(sessions, activeId) {
    sessionList.innerHTML = '';
    if (!sessions || sessions.length === 0) {
        sessionList.innerHTML = '<div style="padding:8px 10px;color:var(--text-muted);font-size:12px;font-style:italic">No sessions yet</div>';
        return;
    }
    sessions.forEach(s => {
        const div = document.createElement('div');
        div.className = 'session-item' + (s.session_id === activeId ? ' active' : '');
        div.innerHTML = `
            <span class="session-icon">ðŸ’¬</span>
            <span class="session-title">${escapeHtml(s.title || 'Untitled')}</span>
            ${s.session_id !== activeId ? '<button class="session-delete" title="Delete">âœ•</button>' : ''}
        `;
        div.addEventListener('click', (e) => {
            if (e.target.classList.contains('session-delete')) {
                deleteSession(s.session_id);
                return;
            }
            switchSession(s.session_id);
        });
        sessionList.appendChild(div);
    });
}

async function switchSession(sessionId) {
    try {
        const res = await fetch(`${API}/sessions/switch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId }),
        });
        const data = await res.json();
        currentSessionId = data.session_id;
        messageHistoryLength = 0;
        chatMessages.innerHTML = '';
        reAddWelcome();
        await loadSessionState();
        await loadHistory();
        await loadFiles();
        await loadSessions();
        showToast(`Switched to: ${data.title}`, 'success');
    } catch (err) {
        showToast('Failed to switch session', 'error');
    }
}

async function newSession() {
    try {
        const res = await fetch(`${API}/sessions/new`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: 'New Chat' }),
        });
        const data = await res.json();
        currentSessionId = data.session_id;
        messageHistoryLength = 0;
        chatMessages.innerHTML = '';
        reAddWelcome();
        await loadSessionState();
        await loadFiles();
        await loadSessions();
        showToast('New session created', 'success');
    } catch (err) {
        showToast('Failed to create session', 'error');
    }
}

async function deleteSession(sessionId) {
    if (!confirm('Delete this session?')) return;
    try {
        await fetch(`${API}/sessions/${sessionId}`, { method: 'DELETE' });
        await loadSessions();
        showToast('Session deleted', 'success');
    } catch (err) {
        showToast('Failed to delete session', 'error');
    }
}

// â”€â”€â”€ Send Message â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || isStreaming) return;

    if (welcomeScreen) welcomeScreen.style.display = 'none';
    appendMessage('user', text);
    chatInput.value = '';
    chatInput.style.height = 'auto';
    isStreaming = true;
    sendBtn.disabled = true;

    const assistantEl = appendMessage('assistant', '', true);
    const contentEl = assistantEl.querySelector('.msg-content');

    try {
        const response = await fetch(`${API}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text }),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = '';
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                try {
                    const data = JSON.parse(line.slice(6));
                    if (data.error) {
                        contentEl.innerHTML = formatContent(`Error: ${data.error}`);
                        showToast(data.error, 'error');
                        break;
                    }
                    if (data.token) {
                        fullText += data.token;
                        contentEl.innerHTML = formatContent(fullText);
                        scrollToBottom();
                    }
                    if (data.intent === 'EXECUTE') {
                        contentEl.innerHTML = formatContent(data.full_response || fullText);
                        // Trigger orchestrator execution automatically
                        setTimeout(() => {
                            runTask(data.goal);
                        }, 500);
                        break;
                    }
                    if (data.done) {
                        if (data.full_response && !fullText) {
                            fullText = data.full_response;
                        }
                        break;
                    }
                } catch {}
            }
        }

        const typing = assistantEl.querySelector('.typing-indicator');
        if (typing) typing.remove();
        if (fullText) contentEl.innerHTML = formatContent(fullText);

        // Refresh sessions (title may have been auto-set)
        loadSessions();

    } catch (err) {
        contentEl.innerHTML = `<span style="color: var(--accent-red)">Connection error: ${err.message}</span>`;
        showToast('Failed to connect to backend', 'error');
    }

    isStreaming = false;
    sendBtn.disabled = false;
    chatInput.focus();
    scrollToBottom();
}

// â”€â”€â”€ Message Rendering â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function appendMessage(role, content, streaming = false) {
    const div = document.createElement('div');
    div.className = 'message';
    const avatarLabel = role === 'user' ? 'U' : 'âš¡';
    const roleLabel = role === 'user' ? 'You' : 'Reflexion';

    let bodyHTML = '';
    if (streaming && !content) {
        bodyHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    } else {
        bodyHTML = formatContent(content);
    }

    div.innerHTML = `
        <div class="msg-avatar ${role}">${avatarLabel}</div>
        <div class="msg-body">
            <div class="msg-role">${roleLabel}</div>
            <div class="msg-content">${bodyHTML}</div>
        </div>`;

    chatMessages.appendChild(div);
    scrollToBottom();
    return div;
}

function formatContent(text) {
    if (!text) return '';

    // Escape HTML first
    let html = escapeHtml(text);

    // Code blocks with language â†’ artifact-style wrapper
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
        const langLabel = lang || 'text';
        const id = 'cb_' + Math.random().toString(36).slice(2, 8);
        return `<div class="code-block-wrapper">
            <div class="code-block-header">
                <span class="code-block-lang">${langLabel}</span>
                <div class="code-block-actions">
                    <button class="code-block-btn" onclick="copyCode('${id}')">Copy</button>
                </div>
            </div>
            <pre><code id="${id}" class="lang-${langLabel}">${code.trim()}</code></pre>
        </div>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Italic
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Headers
    html = html.replace(/^### (.*?)$/gm, '<h4 style="margin:12px 0 6px;color:var(--accent-cyan)">$1</h4>');
    html = html.replace(/^## (.*?)$/gm, '<h3 style="margin:14px 0 8px;color:var(--accent-violet)">$1</h3>');
    // Lists
    html = html.replace(/^- (.*?)$/gm, '<li style="margin-left:16px;list-style:disc">$1</li>');
    html = html.replace(/^(\d+)\. (.*?)$/gm, '<li style="margin-left:16px;list-style:decimal">$2</li>');
    // Paragraphs
    html = html.split('\n\n').map(p => {
        p = p.trim();
        if (!p) return '';
        if (p.startsWith('<div') || p.startsWith('<h') || p.startsWith('<li') || p.startsWith('<pre')) return p;
        return `<p>${p.replace(/\n/g, '<br>')}</p>`;
    }).join('');

    return html;
}

function escapeHtml(text) {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// â”€â”€â”€ Copy Code â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function copyCode(id) {
    const el = document.getElementById(id);
    if (!el) return;
    navigator.clipboard.writeText(el.textContent).then(() => {
        const btn = el.closest('.code-block-wrapper').querySelector('.code-block-btn');
        btn.textContent = 'âœ“ Copied';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
    });
}

// â”€â”€â”€ File Explorer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async function loadFiles() {
    try {
        const res = await fetch(`${API}/files`);
        const data = await res.json();
        fileTree.innerHTML = '';
        if (!data.files || data.files.length === 0) {
            fileTree.innerHTML = '<div class="file-item" style="color:var(--text-muted);font-style:italic">No files yet</div>';
            return;
        }
        data.files.forEach(f => {
            const item = document.createElement('div');
            item.className = 'file-item';
            const ext = f.path.split('.').pop();
            item.innerHTML = `<span class="file-icon">${getFileIcon(ext)}</span>${f.path}<span class="file-size">${formatSize(f.size)}</span>`;
            item.addEventListener('click', () => openFile(f.path));
            fileTree.appendChild(item);
        });
    } catch { /* silently fail */ }
}

function getFileIcon(ext) {
    const icons = { py:'ðŸ', js:'ðŸ“œ', ts:'ðŸ“˜', html:'ðŸŒ', css:'ðŸŽ¨', json:'ðŸ“‹', md:'ðŸ“', txt:'ðŸ“„', yml:'âš™ï¸', yaml:'âš™ï¸', sh:'âš¡', bat:'âš¡', sql:'ðŸ—ƒï¸', env:'ðŸ”’' };
    return icons[ext] || 'ðŸ“„';
}

function formatSize(bytes) {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1048576) return `${(bytes/1024).toFixed(1)}K`;
    return `${(bytes/1048576).toFixed(1)}M`;
}

async function openFile(path) {
    try {
        const res = await fetch(`${API}/file?path=${encodeURIComponent(path)}`);
        if (!res.ok) throw new Error('File not found');
        const data = await res.json();
        document.querySelectorAll('.file-item').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.file-item').forEach(el => {
            if (el.textContent.includes(path)) el.classList.add('active');
        });
        codeViewerTitle.textContent = path;
        const lines = data.content.split('\n');
        const nums = lines.map((_, i) => i + 1).join('\n');
        const escaped = escapeHtml(data.content);
        codeViewerPre.innerHTML = `<span class="code-line-numbers">${nums}</span>${escaped}`;
        codeViewer.classList.add('open');
    } catch (err) {
        showToast(`Cannot open file: ${err.message}`, 'error');
    }
}

// â”€â”€â”€ Run Task â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
// Run Task
async function runTask(taskGoal = null) {
    const goal = taskGoal || prompt('What should I build?');
    if (!goal) return;
    showToast('Generating plan...', 'success');
    if (!taskGoal) {
        appendMessage('user', goal);
    }
    if (welcomeScreen) welcomeScreen.style.display = 'none';
    try {
        const res = await fetch(`${API}/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ goal }),
        });
        const data = await res.json();

        if (data.auto_executed) {
            appendMessage('assistant', `Execution started: **${data.goal}**

Workspace: \`${data.workspace}\`

Auto-Execute is ON.`);
        } else {
            const assistantEl = appendMessage('assistant', `Plan generated for: **${data.goal}**

Workspace: \`${data.workspace}\`

Auto-Execute is OFF. Review the plan, then approve execution.`);
            const actionRow = document.createElement('div');
            actionRow.style.marginTop = '12px';

            const btnApprove = document.createElement('button');
            btnApprove.className = 'sidebar-btn';
            btnApprove.textContent = 'Approve & Execute';
            btnApprove.style.background = 'var(--accent-cyan)';
            btnApprove.style.color = '#000';

            btnApprove.addEventListener('click', async () => {
                btnApprove.disabled = true;
                btnApprove.textContent = 'Executing...';
                try {
                    const execRes = await fetch(`${API}/run/execute`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            plan: data.plan,
                            task: data.goal,
                            workspace_dir: data.workspace
                        }),
                    });
                    const execData = await execRes.json();
                    appendMessage('assistant', `Execution started! Workspace: \`${execData.workspace}\``);
                } catch (err) {
                    btnApprove.disabled = false;
                    btnApprove.textContent = 'Approve & Execute';
                    showToast(`Execute failed: ${err.message}`, 'error');
                }
            });

            actionRow.appendChild(btnApprove);
            assistantEl.querySelector('.msg-body').appendChild(actionRow);
        }
    } catch (err) {
        showToast(`Run failed: ${err.message}`, 'error');
    }
}

// Session Info
async function showSessionInfo() {
    try {
        const res = await fetch(`${API}/session`);
        const s = await res.json();
        const debugCap = s.max_debug_iterations === 0 ? 'unlimited' : s.max_debug_iterations;
        const info = `**Session:** ${s.session_id}
**Title:** ${s.title || '(untitled)'}
**Mode:** ${s.mode}
**Goal:** ${s.current_goal || '(none)'}
**Workspace:** ${s.workspace_dir || '(none)'}
**Thinking:** ${s.thinking_mode ? 'on' : 'off'}
**Auto Execute:** ${s.auto_execute ? 'on' : 'off'}
**Debug Cap:** ${debugCap}
**Iterations:** ${s.iteration_count}`;
        appendMessage('assistant', info);
        if (welcomeScreen) welcomeScreen.style.display = 'none';
    } catch (err) {
        showToast('Cannot fetch session info', 'error');
    }
}

// Show Models
async function showModels() {
    try {
        const res = await fetch(`${API}/models`);
        const data = await res.json();
        let text = `**Installed Models (${data.installed.length}):**
`;
        data.installed.forEach(m => { text += `- ${m}
`; });
        text += `
**Role Assignments:**
`;
        Object.entries(data.roles).forEach(([role, model]) => {
            text += `- ${role}: \`${model || 'none'}\`
`;
        });
        appendMessage('assistant', text);
        if (welcomeScreen) welcomeScreen.style.display = 'none';
    } catch (err) {
        showToast('Cannot fetch models', 'error');
    }
}

// Load History
async function loadHistory() {
    try {
        const res = await fetch(`${API}/history?last_n=50`);
        const data = await res.json();
        if (!data.messages) {
            return;
        }

        if (data.messages.length !== messageHistoryLength) {
            if (data.messages.length === 0) {
                reAddWelcome();
                messageHistoryLength = 0;
                return;
            }

            renderHistory(data.messages);
            messageHistoryLength = data.messages.length;
            scrollToBottom();
        }
    } catch { /* backend not up yet */ }
}

function renderHistory(messages) {
    chatMessages.innerHTML = '';
    if (welcomeScreen) welcomeScreen.style.display = 'none';

    messages.forEach(msg => {
        const text = msg.content;

        if (text.includes('[FILE UPDATED]')) {
            loadFiles();
        }

        if (text.includes('[ERROR]')) {
            const errorPanel = document.getElementById('error-log-panel');
            if (errorPanel) {
                const errorMatch = text.split('[ERROR]')[1];
                if (errorMatch) {
                    errorPanel.innerHTML = `<div style="padding: 5px;">${escapeHtml(errorMatch.trim())}</div>`;
                }
            }
        }

        appendMessage(msg.role, msg.content);
    });
}

// Utilities
function autoResize() {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + 'px';
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function reAddWelcome() {
    chatMessages.innerHTML = `
        <div class="welcome" id="welcome-screen">
            <div class="welcome-logo">Reflexion</div>
            <div class="welcome-sub">Local-first autonomous coding agent.<br>Tell me what to build, debug, or explore.</div>
            <div class="welcome-prompts">
                <button class="welcome-prompt" data-prompt="Build a REST API with FastAPI and SQLite">Build a REST API</button>
                <button class="welcome-prompt" data-prompt="Create a React dashboard with charts">React dashboard</button>
                <button class="welcome-prompt" data-prompt="Help me debug my current project">Debug my project</button>
                <button class="welcome-prompt" data-prompt="What's in my workspace right now?">My workspace</button>
            </div>
        </div>`;
    document.querySelectorAll('.welcome-prompt').forEach(btn => {
        btn.addEventListener('click', () => { chatInput.value = btn.dataset.prompt; sendMessage(); });
    });
}


// Original author: Harsh Ashar | github.com/doriangraypng
// This file is part of Reflexion. Tampering with attribution is detectable.
