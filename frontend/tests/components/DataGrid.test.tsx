import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DataGrid } from '../../src/components/artifacts/DataGrid';

describe('DataGrid Component', () => {
    it('parses CSV and renders a table', () => {
        const csv = "Name,Age\nAlice,30\nBob,25";
        render(<DataGrid csvData={csv} />);
        
        // Headers
        expect(screen.getByText('Name')).toBeDefined();
        expect(screen.getByText('Age')).toBeDefined();
        
        // Cells
        expect(screen.getByText('Alice')).toBeDefined();
        expect(screen.getByText('30')).toBeDefined();
        expect(screen.getByText('Bob')).toBeDefined();
        expect(screen.getByText('25')).toBeDefined();
    });

    it('handles empty CSV', () => {
        const { container } = render(<DataGrid csvData="" />);
        expect(container.querySelector('table')).toBeNull();
    });
});
