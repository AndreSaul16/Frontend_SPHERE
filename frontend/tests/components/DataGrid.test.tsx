import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DataGrid } from '../../src/components/artifacts/DataGrid';
import type { Artifact } from '../../src/types/artifact';

const makeArtifact = (content: string): Artifact => ({
    id: 'grid-1',
    type: 'data_table',
    title: 'Data',
    content,
    createdAt: new Date(),
});

describe('DataGrid Component', () => {
    it('parses a markdown table and renders it', () => {
        // DataGrid now takes a single `artifact` prop and parses a MARKDOWN table
        // (pipe-delimited), not raw CSV.
        const table = `| Name | Age |
|------|-----|
| Alice | 30 |
| Bob | 25 |`;
        render(<DataGrid artifact={makeArtifact(table)} />);

        // Headers
        expect(screen.getByText('Name')).toBeDefined();
        expect(screen.getByText('Age')).toBeDefined();

        // Cells
        expect(screen.getByText('Alice')).toBeDefined();
        expect(screen.getByText('30')).toBeDefined();
        expect(screen.getByText('Bob')).toBeDefined();
        expect(screen.getByText('25')).toBeDefined();
    });

    it('handles empty content', () => {
        // No parseable rows -> renders the "datos incompletos" placeholder, no table.
        const { container } = render(<DataGrid artifact={makeArtifact('')} />);
        expect(container.querySelector('table')).toBeNull();
    });
});
