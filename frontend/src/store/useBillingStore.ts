import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

type PlanId = 'free' | 'starter' | 'premium';
type PaywallReason = '402' | 'upgrade_cta' | 'rag_full' | 'agents_full';

interface BillingState {
  plan_id: PlanId;
  status: 'active' | 'past_due' | 'canceled';
  pro_messages_balance: number;
  topup_messages_balance: number;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  rag_storage_bytes_used: number;
  custom_agents_count: number;
  loaded: boolean;

  paywall: { open: boolean; reason: PaywallReason | null };

  refresh: () => Promise<void>;
  openPaywall: (reason: PaywallReason) => void;
  closePaywall: () => void;
  decrementOptimistic: () => void;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

async function authHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  try {
    const { getAuth } = await import('firebase/auth');
    const auth = getAuth();
    const user = auth.currentUser;
    if (user) {
      headers['Authorization'] = `Bearer ${await user.getIdToken()}`;
    }
  } catch {
    // sin auth aún → endpoint devolverá 401
  }
  return headers;
}

export const useBillingStore = create<BillingState>()(
  devtools(
    (set, get) => ({
      plan_id: 'free',
      status: 'active',
      pro_messages_balance: 0,
      topup_messages_balance: 0,
      current_period_end: null,
      cancel_at_period_end: false,
      rag_storage_bytes_used: 0,
      custom_agents_count: 0,
      loaded: false,

      paywall: { open: false, reason: null },

      refresh: async () => {
        try {
          const headers = await authHeaders();
          const res = await fetch(`${API_URL}/billing/me`, { headers });
          if (!res.ok) {
            console.warn('billing/me failed', res.status);
            return;
          }
          const data = await res.json();
          set({
            plan_id: data.plan_id ?? 'free',
            status: data.status ?? 'active',
            pro_messages_balance: data.pro_messages_balance ?? 0,
            topup_messages_balance: data.topup_messages_balance ?? 0,
            current_period_end: data.current_period_end ?? null,
            cancel_at_period_end: data.cancel_at_period_end ?? false,
            rag_storage_bytes_used: data.rag_storage_bytes_used ?? 0,
            custom_agents_count: data.custom_agents_count ?? 0,
            loaded: true,
          });
        } catch (error) {
          console.error('Failed to refresh billing state', error);
        }
      },

      openPaywall: (reason) => {
        set({ paywall: { open: true, reason } });
      },

      closePaywall: () => {
        set({ paywall: { open: false, reason: null } });
      },

      decrementOptimistic: () => {
        const state = get();
        if (state.pro_messages_balance > 0) {
          set({ pro_messages_balance: state.pro_messages_balance - 1 });
        } else if (state.topup_messages_balance > 0) {
          set({ topup_messages_balance: state.topup_messages_balance - 1 });
        }
      },
    }),
    { name: 'BillingStore' }
  )
);
