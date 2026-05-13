import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CodeBlock } from '../../src/components/artifacts/CodeBlock';

describe('CodeBlock Component', () => {
    it('renders the code content', () => {
        const code = `function test() { return true; }`;
        render(<CodeBlock code={code} language="javascript" />);
        
        // The component should render the raw code or formatted code.
        // We look for parts of the code.
        expect(screen.getByText(/function test/)).toBeDefined();
    });

    it('handles copy button (basic render check)', () => {
        render(<CodeBlock code="const a = 1;" language="typescript" />);
        // Usually a copy button exists
        const buttons = screen.getAllByRole('button');
        expect(buttons.length).toBeGreaterThan(0);
    });
});
