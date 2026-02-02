// Artifact Types for SPHERE Workspace

export type ArtifactType = 'code' | 'markdown' | 'mermaid' | 'data_table' | 'svg';

export interface Artifact {
    id: string;
    type: ArtifactType;
    title: string;
    content: string;
    language?: string; // For code artifacts (python, javascript, etc.)
    agentId?: string;
    createdAt: Date;
}

// Language extensions for download
export const LANGUAGE_EXTENSIONS: Record<string, string> = {
    python: '.py',
    javascript: '.js',
    typescript: '.ts',
    jsx: '.jsx',
    tsx: '.tsx',
    html: '.html',
    css: '.css',
    json: '.json',
    yaml: '.yaml',
    sql: '.sql',
    bash: '.sh',
    shell: '.sh',
    markdown: '.md',
    mermaid: '.mmd',
};

export const getDownloadExtension = (artifact: Artifact): string => {
    if (artifact.type === 'data_table') return '.csv';
    if (artifact.type === 'markdown') return '.md';
    if (artifact.type === 'mermaid') return '.mmd';
    if (artifact.type === 'svg') return '.svg';
    if (artifact.type === 'code' && artifact.language) {
        return LANGUAGE_EXTENSIONS[artifact.language] || '.txt';
    }
    return '.txt';
};
