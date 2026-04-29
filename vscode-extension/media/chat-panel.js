// ╔══════════════════════════════════════════════════════════╗
// ║  Niggativity — Created by Harsh Ashar                        ║
// ║  github.com/Devil1416                                    ║
// ║  Unauthorized reproduction is noticed.                   ║
// ╚══════════════════════════════════════════════════════════╝
const vscode = acquireVsCodeApi();

// ─── fingerprint ────────────────────────────────────────────
const _PROVENANCE = {
    author: "Harsh Ashar",
    github: "github.com/Devil1416",
    project: "Niggativity",
    integrity: "a363c2dddd0d",
};
// ─── /fingerprint ───────────────────────────────────────────

const API = 'http://localhost:8000';

document.addEventListener('DOMContentLoaded', () => {
    const chatHistory = document.getElementById('chat-history');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const runTaskBtn = document.getElementById('run-task-btn');

    let isStreaming = false;

    // Handle messages from the extension host
    window.addEventListener('message', event => {
        const message = event.data;
        switch (message.type) {
            case 'triggerRunTask':
                handleRunTask();
                break;
            case 'sendPrompt':
                chatInput.value = message.value;
                sendMessage();
                break;
        }
    });

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendBtn.addEventListener('click', sendMessage);
    runTaskBtn.addEventListener('click', handleRunTask);

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text || isStreaming) return;

        appendMessage('user', text);
        chatInput.value = '';
        isStreaming = true;
        sendBtn.disabled = true;

        const assistantEl = appendMessage('assistant', '...', true);
        const contentEl = assistantEl.querySelector('.message-content');

        try {
            const response = await fetch(`${API}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

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
                            vscode.postMessage({ type: 'showError', value: data.error });
                            break;
                        }
                        if (data.token) {
                            fullText += data.token;
                            contentEl.innerHTML = formatContent(fullText);
                            scrollToBottom();
                        }
                        if (data.done) break;
                    } catch (e) {
                        console.error('Error parsing SSE data', e);
                    }
                }
            }

            if (fullText) {
                contentEl.innerHTML = formatContent(fullText);
                
                // Extract code blocks to send back to extension for insertion
                const codeBlocks = fullText.match(/\`\`\`[\s\S]*?\`\`\`/g);
                if (codeBlocks && codeBlocks.length > 0) {
                    // Send the last code block (without backticks)
                    let cleanCode = codeBlocks[codeBlocks.length - 1].replace(/\`\`\`\w*\n?/, '').replace(/\`\`\`$/, '').trim();
                    vscode.postMessage({ type: 'codeResponse', value: cleanCode });
                }
            }
        } catch (err) {
            contentEl.innerHTML = `<span style="color: red">Connection error: ${err.message}. Is the backend running?</span>`;
            vscode.postMessage({ type: 'showError', value: 'Failed to connect to backend' });
        }

        isStreaming = false;
        sendBtn.disabled = false;
        chatInput.focus();
        scrollToBottom();
    }

    async function handleRunTask() {
        const goal = chatInput.value.trim();
        if (!goal) {
            vscode.postMessage({ type: 'showInfo', value: 'Please describe the task in the input box first.' });
            return;
        }

        appendMessage('user', `[Run Task] ${goal}`);
        chatInput.value = '';

        try {
            const res = await fetch(`${API}/run`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ goal }),
            });
            const data = await res.json();
            appendMessage('assistant', `🚀 Execution started: **${data.goal}**\n\nWorkspace: \`${data.workspace}\``);
        } catch (err) {
            appendMessage('assistant', `Error starting task: ${err.message}`);
        }
    }

    function appendMessage(role, content, streaming = false) {
        const div = document.createElement('div');
        div.className = `message ${role}`;
        
        const roleLabel = role === 'user' ? 'You' : 'Niggativity';
        
        div.innerHTML = `
            <strong>${roleLabel}</strong>
            <div class="message-content">${formatContent(content)}</div>
        `;

        chatHistory.appendChild(div);
        scrollToBottom();
        return div;
    }

    function formatContent(text) {
        if (!text) return '';
        let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        html = html.replace(/\`\`\`(\w*)\n([\s\S]*?)\`\`\`/g, (_, lang, code) => {
            return `<pre><code class="lang-${lang || 'text'}">${code.trim()}</code></pre>`;
        });
        html = html.replace(/\`([^\`]+)\`/g, '<code>$1</code>');
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        html = html.split('\n\n').map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');
        return html;
    }

    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
});


// Original author: Harsh Ashar | github.com/Devil1416
// This file is part of Niggativity. Tampering with attribution is detectable.
