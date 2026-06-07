import { describe, it, expect, vi } from 'vitest';
import { render, waitFor } from '@testing-library/react';
import { MermaidDiagram } from '../../src/components/artifacts/MermaidDiagram';
import type { Artifact } from '../../src/types/artifact';

// Mock mermaid to avoid actual DOM manipulation issues in JSDOM
vi.mock('mermaid', () => ({
    default: {
        initialize: vi.fn(),
        render: vi.fn().mockResolvedValue({ svg: '<svg><g>mocked-diagram</g></svg>' }),
    }
}));

const makeArtifact = (content: string): Artifact => ({
    id: 'mermaid-1',
    type: 'mermaid',
    title: 'Diagram',
    content,
    createdAt: new Date(),
});

describe('MermaidDiagram Component', () => {
    it('renders without crashing and displays the container', () => {
        // MermaidDiagram now takes a single `artifact` prop. The diagram is rendered
        // into a div with the `mermaid-container` class.
        const { container } = render(<MermaidDiagram artifact={makeArtifact('graph TD; A-->B;')} />);
        expect(container.querySelector('.mermaid-container')).not.toBeNull();
    });

    it('injects the rendered svg from mermaid', async () => {
        const { container } = render(<MermaidDiagram artifact={makeArtifact('graph TD; A-->B;')} />);
        // The async render effect injects the mocked svg into the container.
        await waitFor(() => {
            expect(container.querySelector('svg')).not.toBeNull();
        });
    });
});
