const vscode = require('vscode');
const path   = require('path');
const fs     = require('fs');

function activate(context) {

  // ── Run Current File ──────────────────────────────────
  const runCmd = vscode.commands.registerCommand('fsn.runFile', () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showErrorMessage('No active file to run.');
      return;
    }

    const doc = editor.document;
    if (doc.isDirty) {
      doc.save();
    }

    const filePath    = doc.fileName;
    const config      = vscode.workspace.getConfiguration('fsn');
    const pythonPath  = config.get('pythonPath') || 'python3';

    // Resolve interpreter: user setting → bundled fsn.py next to extension
    let interpPath = config.get('interpreterPath') || '';
    if (!interpPath) {
      interpPath = path.join(context.extensionPath, 'fsn.py');
    }

    if (!fs.existsSync(interpPath)) {
      vscode.window.showErrorMessage(
        `FSN interpreter not found at: ${interpPath}\n` +
        `Set fsn.interpreterPath in settings or place fsn.py next to the extension.`
      );
      return;
    }

    // Create or reuse terminal
    let terminal = vscode.window.terminals.find(t => t.name === 'FSN');
    if (!terminal) {
      terminal = vscode.window.createTerminal({ name: 'FSN' });
    }
    terminal.show(true);
    terminal.sendText(`${pythonPath} "${interpPath}" "${filePath}"`);
  });

  // ── Open REPL ─────────────────────────────────────────
  const replCmd = vscode.commands.registerCommand('fsn.openRepl', () => {
    const config     = vscode.workspace.getConfiguration('fsn');
    const pythonPath = config.get('pythonPath') || 'python3';
    let interpPath   = config.get('interpreterPath') || '';
    if (!interpPath) {
      interpPath = path.join(context.extensionPath, 'fsn.py');
    }

    if (!fs.existsSync(interpPath)) {
      vscode.window.showErrorMessage(
        `FSN interpreter not found at: ${interpPath}`
      );
      return;
    }

    const terminal = vscode.window.createTerminal({ name: 'FSN REPL' });
    terminal.show();
    terminal.sendText(`${pythonPath} "${interpPath}"`);
  });

  // ── Status bar item ───────────────────────────────────
  const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  statusBar.command = 'fsn.runFile';
  statusBar.text    = '$(play) Run FSN';
  statusBar.tooltip = 'Run this .fsn file (Ctrl+F5)';

  const updateStatusBar = () => {
    const editor = vscode.window.activeTextEditor;
    if (editor && editor.document.languageId === 'fsn') {
      statusBar.show();
    } else {
      statusBar.hide();
    }
  };

  vscode.window.onDidChangeActiveTextEditor(updateStatusBar, null, context.subscriptions);
  updateStatusBar();

  context.subscriptions.push(runCmd, replCmd, statusBar);
}

function deactivate() {}

module.exports = { activate, deactivate };
