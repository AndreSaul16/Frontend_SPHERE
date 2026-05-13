import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import { MermaidDiagram } from '../../src/components/artifacts/MermaidDiagram';

// Mock mermaid to avoid actual DOM manipulation issues in JSDOM
vi.mock('mermaid', () => ({
    default: {
        initialize: vi.fn(),
        render: vi.fn().mockResolvedValue({ svg: '<svg><g>mocked-diagram</g></svg>' }),
    }
}));

describe('MermaidDiagram Component', () => {
    it('renders without crashing and displays the container', () => {
        const { container } = render(<MermaidDiagram chart="graph TD; A-->B;" />);
        expect(container.querySelector('.mermaid')).toBeDefined();
    });
});
