import * as vscode from 'vscode';
import { exec } from 'child_process';

export function activate(context: vscode.ExtensionContext) {
    console.log('Notebook Close Runner activated');

    vscode.workspace.onDidCloseNotebookDocument((notebook: vscode.NotebookDocument) => {
        const notebookPath = notebook.uri.fsPath;
        console.log(`Notebook closed: ${notebookPath}`);

        // Read the script path from VS Code settings
        const pythonScript = vscode.workspace
            .getConfiguration('notebookCloseRunner')
            .get<string>('pythonScript');

        if (!pythonScript) {
            console.error('No Python script configured in settings.');
            return;
        }

        exec(`python3 "${pythonScript}" "${notebookPath}"`, (error, stdout, stderr) => {
            if (error) {
                console.error(`Error running the script: ${error.message}`);
                return;
            }
            if (stdout) console.log(`Output: ${stdout}`);
            if (stderr) console.error(`Error: ${stderr}`);
        });
    });
}

export function deactivate() {
    console.log('Notebook Close Runner deactivated');
}