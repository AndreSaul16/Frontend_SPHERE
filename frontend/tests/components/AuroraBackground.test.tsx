import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { AuroraBackground } from '../../src/components/AuroraBackground';

describe('AuroraBackground Animation Component', () => {
    it('renders the animated container elements', () => {
        const { container } = render(<AuroraBackground />);
        
        // Assert that the container div is present and has the base styling
        const mainDiv = container.firstChild as HTMLElement;
        expect(mainDiv).toBeDefined();
        expect(mainDiv.className).toContain('fixed inset-0 z-[-1] overflow-hidden bg-[#0A0A10]');
        
        // Assert inner animated blobs exist
        const blobs = mainDiv.querySelectorAll('div.absolute');
        expect(blobs.length).toBeGreaterThan(0);
        
        // Assert animation classes exist (mix-blend-screen, blur, animate-blob)
        const firstBlob = blobs[0] as HTMLElement;
        expect(firstBlob.className).toContain('animate-blob');
        expect(firstBlob.className).toContain('mix-blend-screen');
    });
});
