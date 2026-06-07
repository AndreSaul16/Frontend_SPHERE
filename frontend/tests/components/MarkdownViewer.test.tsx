import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MarkdownViewer } from '../../src/components/artifacts/MarkdownViewer';
import type { Artifact } from '../../src/types/artifact';

const makeArtifact = (content: string): Artifact => ({
    id: 'md-1',
    type: 'markdown',
    title: 'Doc',
    content,
    createdAt: new Date(),
});

describe('MarkdownViewer Component', () => {
    it('renders markdown content', () => {
        // MarkdownViewer now takes a single `artifact` prop.
        render(<MarkdownViewer artifact={makeArtifact('# Heading 1\n\nSome paragraph text')} />);
        // The markdown parser should render a heading and a paragraph
        expect(screen.getByText('Heading 1')).toBeDefined();
        expect(screen.getByText('Some paragraph text')).toBeDefined();
    });

    it('renders tables correctly', () => {
        const mdTable = `
| A | B |
|---|---|
| 1 | 2 |
        `;
        render(<MarkdownViewer artifact={makeArtifact(mdTable)} />);
        expect(screen.getByText('A')).toBeDefined();
        expect(screen.getByText('B')).toBeDefined();
        expect(screen.getByText('1')).toBeDefined();
        expect(screen.getByText('2')).toBeDefined();
    });
});
