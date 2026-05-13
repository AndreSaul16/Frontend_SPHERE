import { describe, it, expect, beforeEach } from 'vitest';
import { useBillingStore } from '../../src/store/useBillingStore';

describe('useBillingStore', () => {
    beforeEach(() => {
        // Reset the store state before each test
        useBillingStore.setState({
            plan_id: 'free',
            pro_messages_balance: 5,
            topup_messages_balance: 0,
            current_period_end: '',
            rag_storage_used_mb: 0,
            custom_agents_count: 0,
            paywall: { open: false, reason: null }
        });
    });

    it('should initialize with default free plan values', () => {
        const state = useBillingStore.getState();
        expect(state.plan_id).toBe('free');
        expect(state.pro_messages_balance).toBe(5);
        expect(state.topup_messages_balance).toBe(0);
        expect(state.paywall.open).toBe(false);
    });

    it('should open and close the paywall', () => {
        useBillingStore.getState().openPaywall('402');
        let state = useBillingStore.getState();
        expect(state.paywall.open).toBe(true);
        expect(state.paywall.reason).toBe('402');

        useBillingStore.getState().closePaywall();
        state = useBillingStore.getState();
        expect(state.paywall.open).toBe(false);
        expect(state.paywall.reason).toBe(null);
    });

    it('should decrement pro_messages_balance optimistically if > 0', () => {
        useBillingStore.getState().decrementOptimistic();
        expect(useBillingStore.getState().pro_messages_balance).toBe(4);
        expect(useBillingStore.getState().topup_messages_balance).toBe(0);
    });

    it('should decrement topup_messages_balance optimistically if pro is 0', () => {
        useBillingStore.setState({ pro_messages_balance: 0, topup_messages_balance: 10 });
        useBillingStore.getState().decrementOptimistic();
        expect(useBillingStore.getState().pro_messages_balance).toBe(0);
        expect(useBillingStore.getState().topup_messages_balance).toBe(9);
    });
});
