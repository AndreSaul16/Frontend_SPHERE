import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CreditsIndicator } from '../../src/components/CreditsIndicator';
import { useBillingStore } from '../../src/store/useBillingStore';

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
}));

describe('CreditsIndicator Component', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        useBillingStore.setState({
            plan_id: 'free',
            pro_messages_balance: 5,
            topup_messages_balance: 0,
        });
    });

    it('renders balances correctly', () => {
        useBillingStore.setState({
            pro_messages_balance: 100,
            topup_messages_balance: 50,
        });
        render(<CreditsIndicator />);
        expect(screen.getByText('100')).toBeDefined();
        expect(screen.getByText('+50')).toBeDefined();
    });

    it('navigates to billing on click', () => {
        render(<CreditsIndicator />);
        const indicator = screen.getByTestId('credits-indicator');
        fireEvent.click(indicator);
        expect(mockNavigate).toHaveBeenCalledWith('/billing');
    });

    it('hides topup balance if zero', () => {
        useBillingStore.setState({
            pro_messages_balance: 100,
            topup_messages_balance: 0,
        });
        render(<CreditsIndicator />);
        expect(screen.getByText('100')).toBeDefined();
        expect(screen.queryByText('+0')).toBeNull();
    });

    describe('Plan tier display', () => {
        it('shows "Free" tier for free users', () => {
            useBillingStore.setState({
                plan_id: 'free',
                pro_messages_balance: 3,
                topup_messages_balance: 0,
            });
            render(<CreditsIndicator />);
            // Should display the plan tier
            expect(screen.getByText(/Free/i)).toBeDefined();
        });

        it('shows "Starter" tier for starter users', () => {
            useBillingStore.setState({
                plan_id: 'starter',
                pro_messages_balance: 42,
                topup_messages_balance: 0,
            });
            render(<CreditsIndicator />);
            expect(screen.getByText(/Starter/i)).toBeDefined();
        });

        it('shows "Premium" tier for premium users', () => {
            useBillingStore.setState({
                plan_id: 'premium',
                pro_messages_balance: 99,
                topup_messages_balance: 0,
            });
            render(<CreditsIndicator />);
            expect(screen.getByText(/Premium/i)).toBeDefined();
        });

        it('shows call-to-action when balance is zero', () => {
            useBillingStore.setState({
                plan_id: 'free',
                pro_messages_balance: 0,
                topup_messages_balance: 0,
            });
            render(<CreditsIndicator />);
            // Should show "Recargar" CTA
            expect(screen.getByText(/Recargar/i)).toBeDefined();
        });

        it('shows remaining count with plan tier (free user format)', () => {
            useBillingStore.setState({
                plan_id: 'free',
                pro_messages_balance: 3,
                topup_messages_balance: 0,
            });
            render(<CreditsIndicator />);
            // Should show something like "3/5 Free" or "3 Free"
            expect(screen.getByText('3')).toBeDefined();
            expect(screen.getByText(/Free/i)).toBeDefined();
        });
    });
});
