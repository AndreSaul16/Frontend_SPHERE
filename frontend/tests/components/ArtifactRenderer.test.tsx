import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ArtifactRenderer } from '../../src/components/artifacts/ArtifactRenderer';

// Mock the child components to simplify testing
vi.mock('../../src/components/artifacts/CodeBlock', () => ({
    CodeBlock: ({ code }: { code: string }) => <div data-testid="code-block">{code}</div>
}));
vi.mock('../../src/components/artifacts/MarkdownViewer', () => ({
    MarkdownViewer: ({ content }: { content: string }) => <div data-testid="markdown-viewer">{content}</div>
}));
vi.mock('../../src/components/artifacts/MermaidDiagram', () => ({
    MermaidDiagram: ({ chart }: { chart: string }) => <div data-testid="mermaid-diagram">{chart}</div>
}));
vi.mock('../../src/components/artifacts/DataGrid', () => ({
    DataGrid: ({ csvData }: { csvData: string }) => <div data-testid="data-grid">{csvData}</div>
}));

describe('ArtifactRenderer Component', () => {
    it('renders CodeBlock for code artifact type', () => {
        render(<ArtifactRenderer type="code" content="const a = 1;" language="typescript" />);
        expect(screen.getByTestId('code-block')).toBeDefined();
        expect(screen.getByText('const a = 1;')).toBeDefined();
    });

    it('renders MarkdownViewer for markdown artifact type', () => {
        render(<ArtifactRenderer type="markdown" content="# Hello" language="" />);
        expect(screen.getByTestId('markdown-viewer')).toBeDefined();
        expect(screen.getByText('# Hello')).toBeDefined();
    });

    it('renders MermaidDiagram for mermaid artifact type', () => {
        render(<ArtifactRenderer type="mermaid" content="graph TD;" language="" />);
        expect(screen.getByTestId('mermaid-diagram')).toBeDefined();
        expect(screen.getByText('graph TD;')).toBeDefined();
    });

    it('renders DataGrid for csv artifact type', () => {
        render(<ArtifactRenderer type="csv" content="a,b\n1,2" language="" />);
        expect(screen.getByTestId('data-grid')).toBeDefined();
        expect(screen.getByText('a,b\n1,2')).toBeDefined();
    });

    it('renders CodeBlock as fallback for unknown type', () => {
        render(<ArtifactRenderer type="unknown_type" content="foo" language="" />);
        expect(screen.getByTestId('code-block')).toBeDefined();
        expect(screen.getByText('foo')).toBeDefined();
    });
});
