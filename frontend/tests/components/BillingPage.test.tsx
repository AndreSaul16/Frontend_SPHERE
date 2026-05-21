import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BillingPage } from '../../src/pages/BillingPage';
import { useBillingStore } from '../../src/store/useBillingStore';

// Mock firebase/auth to prevent dynamic import from failing
vi.mock('firebase/auth', () => ({
    getAuth: vi.fn(() => ({
        currentUser: {
            getIdToken: vi.fn(() => Promise.resolve('mock-token')),
        },
    })),
}));

describe('BillingPage - Loading / Error / Stripe States (Task 2.3)', () => {
    beforeEach(() => {
        useBillingStore.setState({
            plan_id: 'free',
            status: 'active',
            pro_messages_balance: 5,
            topup_messages_balance: 0,
            current_period_end: null,
            cancel_at_period_end: false,
            loaded: false,
            isLoading: false,
            error: null,
            stripe_configured: true,
            refresh: vi.fn().mockResolvedValue(undefined),
        });
        vi.clearAllMocks();
    });

    it('shows loading skeleton when isLoading and not loaded (BF-002)', () => {
        useBillingStore.setState({ isLoading: true, loaded: false });

        render(<BillingPage />);

        // The page should NOT show plan information while loading
        expect(screen.queryByText('Facturación y Planes')).not.toBeInTheDocument();
        // Should show a loading indicator
        expect(screen.getByTestId('billing-loading')).toBeInTheDocument();
    });

    it('shows error state with retry button when error is set (BF-001)', () => {
        useBillingStore.setState({
            error: 'Error al cargar la información de facturación',
            isLoading: false,
            loaded: false,
        });

        render(<BillingPage />);

        expect(screen.getByText('Error al cargar la información de facturación')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /reintentar/i })).toBeInTheDocument();
    });

    it('retry button calls refresh when clicked (BF-001)', () => {
        const mockRefresh = vi.fn().mockResolvedValue(undefined);
        useBillingStore.setState({
            error: 'Error al cargar la información de facturación',
            isLoading: false,
            loaded: false,
            refresh: mockRefresh,
        });

        render(<BillingPage />);

        screen.getByRole('button', { name: /reintentar/i }).click();
        expect(mockRefresh).toHaveBeenCalled();
    });

    it('shows "Pagos no disponibles" when stripe_configured is false (BF-004)', () => {
        useBillingStore.setState({
            stripe_configured: false,
            loaded: true,
            isLoading: false,
            plan_id: 'free',
            pro_messages_balance: 5,
        });

        render(<BillingPage />);

        expect(screen.getByText(/Pagos no disponibles/i)).toBeInTheDocument();
        // Subscription buttons should be hidden
        expect(screen.queryByText('Suscribirse')).not.toBeInTheDocument();
    });

    it('shows plan content when loaded=true and no error (BF-002)', () => {
        useBillingStore.setState({
            loaded: true,
            isLoading: false,
            error: null,
            plan_id: 'starter',
            pro_messages_balance: 100,
            topup_messages_balance: 50,
            stripe_configured: true,
        });

        render(<BillingPage />);

        expect(screen.getByText('Facturación y Planes')).toBeInTheDocument();
        expect(screen.getByText('starter')).toBeInTheDocument();
        expect(screen.getByText('100')).toBeInTheDocument();
    });

    it('shows alert on checkout failure (BF-004)', async () => {
        const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {});
        global.fetch = vi.fn().mockResolvedValue({
            ok: false,
            status: 500,
            text: () => Promise.resolve('Internal Server Error'),
        }) as any;

        useBillingStore.setState({
            loaded: true,
            isLoading: false,
            stripe_configured: true,
            plan_id: 'free',
        });

        render(<BillingPage />);

        // Click the "Suscribirse" button on the Starter plan
        const subscribeButtons = screen.getAllByText('Suscribirse');
        subscribeButtons[0].click();

        // Wait for fetch to reject and alert to be called
        await vi.waitFor(() => {
            expect(alertSpy).toHaveBeenCalledWith(
                expect.stringContaining('Error al procesar el pago')
            );
        });

        alertSpy.mockRestore();
    });
});
