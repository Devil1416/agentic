// ╔══════════════════════════════════════════════════════════╗
// ║  Reflexion — Created by Harsh Ashar                        ║
// ║  github.com/doriangraypng                                    ║
// ║  Unauthorized reproduction is noticed.                   ║
// ╚══════════════════════════════════════════════════════════╝
const vscode = require('vscode');

// ─── fingerprint ────────────────────────────────────────────
const _PROVENANCE = {
    author: "Harsh Ashar",
    github: "github.com/doriangraypng",
    project: "Reflexion",
    integrity: "1f1411b85242",
};
// ─── /fingerprint ───────────────────────────────────────────


/**
 * Main Extension Logic
 */
function activate(context) {
    console.log('Reflexion extension is now active');

    const provider = new ReflexionViewProvider(context.extensionUri);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider('reflexion-chat', provider)
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('reflexion.sendMessage', () => {
            vscode.commands.executeCommand('reflexion-chat.focus');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('reflexion.runTask', () => {
            vscode.commands.executeCommand('reflexion-chat.focus');
            provider.postMessageToWebview({ type: 'triggerRunTask' });
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('reflexion.insertCode', async () => {
            const editor = vscode.window.activeTextEditor;
            if (editor && provider.lastCodeResponse) {
                editor.edit(editBuilder => {
                    editBuilder.insert(editor.selection.active, provider.lastCodeResponse);
                });
            } else {
                vscode.window.showInformationMessage('No recent code available or no active editor.');
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('reflexion.optimizeSelection', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) return;

            const selection = editor.selection;
            const text = editor.document.getText(selection);

            if (!text) {
                vscode.window.showInformationMessage('Please select some code to optimize.');
                return;
            }

            vscode.commands.executeCommand('reflexion-chat.focus');
            
            const prompt = `Please optimize this code. Only return the updated code, no explanations:\n\n\`\`\`\n${text}\n\`\`\``;
            
            provider.postMessageToWebview({ type: 'sendPrompt', value: prompt });
            provider.pendingReplacementSelection = selection;
        })
    );
}

class ReflexionViewProvider {
    constructor(extensionUri) {
        this._extensionUri = extensionUri;
        this._view = null;
        this.lastCodeResponse = null;
        this.pendingReplacementSelection = null;
    }

    resolveWebviewView(webviewView, context, token) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        webviewView.webview.onDidReceiveMessage(data => {
            switch (data.type) {
                case 'codeResponse':
                    this.lastCodeResponse = data.value;
                    if (this.pendingReplacementSelection) {
                        const editor = vscode.window.activeTextEditor;
                        if (editor) {
                            editor.edit(editBuilder => {
                                editBuilder.replace(this.pendingReplacementSelection, data.value);
                            });
                            this.pendingReplacementSelection = null;
                        }
                    }
                    break;
                case 'showInfo':
                    vscode.window.showInformationMessage(data.value);
                    break;
                case 'showError':
                    vscode.window.showErrorMessage(data.value);
                    break;
                case 'readFile':
                    this.handleReadFile(data.path);
                    break;
            }
        });
    }

    async handleReadFile(filePath) {
        try {
            const document = await vscode.workspace.openTextDocument(filePath);
            this.postMessageToWebview({
                type: 'fileContent',
                path: filePath,
                content: document.getText()
            });
        } catch (err) {
            this.postMessageToWebview({
                type: 'showError',
                value: `Could not read file: ${err.message}`
            });
        }
    }

    postMessageToWebview(message) {
        if (this._view) {
            this._view.webview.postMessage(message);
        }
    }

    _getHtmlForWebview(webview) {
        const scriptUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, 'media', 'chat-panel.js')
        );

        return `<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Reflexion Chat</title>
                <style>
                    body {
                        font-family: var(--vscode-font-family);
                        color: var(--vscode-editor-foreground);
                        background-color: var(--vscode-editor-background);
                        margin: 0;
                        padding: 10px;
                        display: flex;
                        flex-direction: column;
                        height: 100vh;
                        box-sizing: border-box;
                    }
                    #chat-history {
                        flex: 1;
                        overflow-y: auto;
                        margin-bottom: 10px;
                    }
                    .message {
                        margin-bottom: 10px;
                        padding: 8px;
                        border-radius: 4px;
                    }
                    .message.user {
                        background-color: var(--vscode-editor-inactiveSelectionBackground);
                    }
                    .message.assistant {
                        background-color: var(--vscode-editor-selectionBackground);
                    }
                    .message-content pre {
                        background-color: var(--vscode-textCodeBlock-background);
                        padding: 8px;
                        border-radius: 4px;
                        overflow-x: auto;
                    }
                    .message-content code {
                        font-family: var(--vscode-editor-font-family);
                        font-size: 0.9em;
                    }
                    #input-container {
                        display: flex;
                        flex-direction: column;
                        gap: 8px;
                        padding-bottom: 10px;
                    }
                    textarea {
                        width: 100%;
                        background-color: var(--vscode-input-background);
                        color: var(--vscode-input-foreground);
                        border: 1px solid var(--vscode-input-border);
                        padding: 8px;
                        font-family: var(--vscode-font-family);
                        resize: vertical;
                        min-height: 60px;
                        box-sizing: border-box;
                    }
                    .button-row {
                        display: flex;
                        gap: 8px;
                    }
                    button {
                        background-color: var(--vscode-button-background);
                        color: var(--vscode-button-foreground);
                        border: none;
                        padding: 6px 12px;
                        cursor: pointer;
                        flex: 1;
                    }
                    button:hover {
                        background-color: var(--vscode-button-hoverBackground);
                    }
                </style>
            </head>
            <body>
                <div id="chat-history">
                    <div class="message assistant">
                        <strong>Reflexion</strong>
                        <div class="message-content">Hello! How can I help you today?</div>
                    </div>
                </div>
                <div id="input-container">
                    <textarea id="chat-input" placeholder="Ask reflexion... (Shift+Enter for new line)"></textarea>
                    <div class="button-row">
                        <button id="send-btn">Send</button>
                        <button id="run-task-btn">Run Task</button>
                    </div>
                </div>
                <script src="${scriptUri}"></script>
            </body>
            </html>`;
    }
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};


// Original author: Harsh Ashar | github.com/doriangraypng
// This file is part of Reflexion. Tampering with attribution is detectable.
