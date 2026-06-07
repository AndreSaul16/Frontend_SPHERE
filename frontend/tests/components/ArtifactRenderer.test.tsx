import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ArtifactRenderer } from '../../src/components/artifacts/ArtifactRenderer';
import type { Artifact } from '../../src/types/artifact';

// Mock the child components to simplify testing.
// The renderer passes the whole `artifact` object down, so the mocks read
// `artifact.content` (and `artifact.type` where useful).
vi.mock('../../src/components/artifacts/CodeBlock', () => ({
    CodeBlock: ({ artifact }: { artifact: Artifact }) => (
        <div data-testid="code-block">{artifact.content}</div>
    )
}));
vi.mock('../../src/components/artifacts/MarkdownViewer', () => ({
    MarkdownViewer: ({ artifact }: { artifact: Artifact }) => (
        <div data-testid="markdown-viewer">{artifact.content}</div>
    )
}));
vi.mock('../../src/components/artifacts/MermaidDiagram', () => ({
    MermaidDiagram: ({ artifact }: { artifact: Artifact }) => (
        <div data-testid="mermaid-diagram">{artifact.content}</div>
    )
}));
vi.mock('../../src/components/artifacts/DataGrid', () => ({
    DataGrid: ({ artifact }: { artifact: Artifact }) => (
        <div data-testid="data-grid">{artifact.content}</div>
    )
}));

const makeArtifact = (overrides: Partial<Artifact>): Artifact => ({
    id: 'a-1',
    type: 'code',
    title: 'Test',
    content: '',
    createdAt: new Date(),
    ...overrides,
});

describe('ArtifactRenderer Component', () => {
    it('renders CodeBlock for code artifact type', () => {
        render(<ArtifactRenderer artifact={makeArtifact({ type: 'code', content: 'const a = 1;', language: 'typescript' })} />);
        expect(screen.getByTestId('code-block')).toBeDefined();
        expect(screen.getByText('const a = 1;')).toBeDefined();
    });

    it('renders MarkdownViewer for markdown artifact type', () => {
        render(<ArtifactRenderer artifact={makeArtifact({ type: 'markdown', content: '# Hello' })} />);
        expect(screen.getByTestId('markdown-viewer')).toBeDefined();
        expect(screen.getByText('# Hello')).toBeDefined();
    });

    it('renders MermaidDiagram for mermaid artifact type', () => {
        render(<ArtifactRenderer artifact={makeArtifact({ type: 'mermaid', content: 'graph TD;' })} />);
        expect(screen.getByTestId('mermaid-diagram')).toBeDefined();
        expect(screen.getByText('graph TD;')).toBeDefined();
    });

    it('renders DataGrid for data_table artifact type', () => {
        render(<ArtifactRenderer artifact={makeArtifact({ type: 'data_table', content: 'a,b\n1,2' })} />);
        const grid = screen.getByTestId('data-grid');
        expect(grid).toBeDefined();
        // getByText normaliza el whitespace (colapsa '\n'), así que verificamos
        // el textContent crudo del nodo en su lugar.
        expect(grid.textContent).toContain('a,b');
        expect(grid.textContent).toContain('1,2');
    });

    it('renders an "unsupported" fallback for unknown type', () => {
        // Unknown types fall through to the default branch, which shows a
        // friendly "no soportado" message plus the raw type string.
        render(<ArtifactRenderer artifact={makeArtifact({ type: 'unknown_type' as any, content: 'foo' })} />);
        expect(screen.getByText(/Tipo de artefacto no soportado/i)).toBeDefined();
        expect(screen.getByText('unknown_type')).toBeDefined();
    });
});
