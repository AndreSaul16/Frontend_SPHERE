import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BillingPage } from '../../src/pages/BillingPage';
import { useBillingStore } from '../../src/store/useBillingStore';

describe('BillingPage Component', () => {
    beforeEach(() => {
        useBillingStore.setState({
            plan_id: 'starter',
            pro_messages_balance: 1000,
            topup_messages_balance: 50,
            current_period_end: new Date().toISOString(),
        });
        
        // Mock the window.fetch
        global.fetch = vi.fn().mockResolvedValue({
            json: () => Promise.resolve({ url: 'http://mock.url' })
        }) as any;
    });

    it('renders the correct plan information', () => {
        render(<BillingPage />);
        expect(screen.getByText('starter')).toBeDefined();
        expect(screen.getByText('1000')).toBeDefined();
        expect(screen.getByText('50')).toBeDefined();
    });

    it('renders available plans', () => {
        render(<BillingPage />);
        expect(screen.getByText('Premium')).toBeDefined();
        expect(screen.getByText('€19.99')).toBeDefined();
        expect(screen.getByText('€9.99')).toBeDefined(); // Starter price
        expect(screen.getByText('Packs Adicionales')).toBeDefined();
    });
});
