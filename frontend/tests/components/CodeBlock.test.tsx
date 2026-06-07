import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CodeBlock } from '../../src/components/artifacts/CodeBlock';
import type { Artifact } from '../../src/types/artifact';

const makeArtifact = (overrides: Partial<Artifact>): Artifact => ({
    id: 'code-1',
    type: 'code',
    title: 'Snippet',
    content: '',
    createdAt: new Date(),
    ...overrides,
});

describe('CodeBlock Component', () => {
    it('renders the code content', () => {
        const code = `function test() { return true; }`;
        // CodeBlock now takes a single `artifact` prop and renders the code through
        // react-syntax-highlighter, which tokenizes the source across many spans.
        // Assert against the combined text content rather than a single text node.
        const { container } = render(
            <CodeBlock artifact={makeArtifact({ content: code, language: 'javascript' })} />
        );
        expect(container.textContent).toContain('function');
        expect(container.textContent).toContain('test');
    });

    it('handles copy button (basic render check)', () => {
        render(<CodeBlock artifact={makeArtifact({ content: 'const a = 1;', language: 'typescript' })} />);
        // The toolbar exposes copy and download buttons.
        const buttons = screen.getAllByRole('button');
        expect(buttons.length).toBeGreaterThan(0);
    });
});
