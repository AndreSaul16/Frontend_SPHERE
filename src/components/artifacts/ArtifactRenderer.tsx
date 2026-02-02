// Artifact Renderer - Master Switch Component
import type { Artifact } from '@/types/artifact';
import { CodeBlock } from './CodeBlock';
import { MarkdownViewer } from './MarkdownViewer';
import { DataGrid } from './DataGrid';
import { MermaidDiagram } from './MermaidDiagram';
import { FileQuestion } from 'lucide-react';

interface ArtifactRendererProps {
    artifact: Artifact;
}

export function ArtifactRenderer({ artifact }: ArtifactRendererProps) {
    switch (artifact.type) {
        case 'code':
            return <CodeBlock artifact={artifact} />;
        case 'markdown':
            return <MarkdownViewer artifact={artifact} />;
        case 'data_table':
            return <DataGrid artifact={artifact} />;
        case 'mermaid':
            return <MermaidDiagram artifact={artifact} />;
        case 'svg':
            return (
                <div className="flex-1 flex items-center justify-center p-4">
                    <div
                        className="max-w-full max-h-full"
                        dangerouslySetInnerHTML={{ __html: artifact.content }}
                    />
                </div>
            );
        default:
            return (
                <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center p-6">
                    <FileQuestion className="h-12 w-12 text-text-secondary" />
                    <p className="text-text-secondary">Tipo de artefacto no soportado</p>
                    <code className="text-xs text-luxury-purple">{artifact.type}</code>
                </div>
            );
    }
}
