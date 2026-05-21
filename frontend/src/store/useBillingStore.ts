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
  isLoading: boolean;
  error: string | null;
  stripe_configured: boolean;

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

/**
 * Espera hasta que Firebase Auth esté inicializado.
 * Polling de `auth.currentUser` cada 100ms, máximo 5s.
 * Si no hay usuario tras 5s, se asume que el auth ya cargó (usuario no logueado).
 */
async function waitForAuthReady(): Promise<void> {
  const startTime = Date.now();
  while (Date.now() - startTime < 5000) {
    try {
      const { getAuth } = await import('firebase/auth');
      const auth = getAuth();
      // auth.currentUser será null durante la inicialización y después
      // si no hay usuario. Polling de 100ms con timeout de 5s asegura
      // que Firebase haya cargado su estado de persistencia.
      if (auth.currentUser) {
        return; // Usuario autenticado, listo
      }
    } catch {
      // Firebase aún no disponible, reintentar
    }
    await new Promise((r) => setTimeout(r, 100));
  }
  // Timeout: asumimos que auth ya está listo (sin usuario)
}

const RETRY_BACKOFFS = [1000, 2000, 4000];
const MAX_RETRIES = RETRY_BACKOFFS.length;

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
      isLoading: false,
      error: null,
      stripe_configured: false,

      paywall: { open: false, reason: null },

      refresh: async () => {
        // Señalizar que está cargando
        set({ isLoading: true, error: null });

        // Esperar a que Firebase Auth esté listo antes del primer fetch
        await waitForAuthReady();

        let lastError: unknown = null;

        for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
          try {
            // Backoff entre intentos (saltamos el delay en el primer intento)
            if (attempt > 0) {
              await new Promise((r) => setTimeout(r, RETRY_BACKOFFS[attempt - 1]));
            }

            const headers = await authHeaders();
            const res = await fetch(`${API_URL}/billing/me`, { headers });

            if (!res.ok) {
              throw new Error(`HTTP ${res.status}`);
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
              stripe_configured: data.stripe_configured ?? false,
              loaded: true,
              isLoading: false,
              error: null,
            });
            return; // Éxito
          } catch (err) {
            lastError = err;
            // Si es el último intento, no reintentamos
            if (attempt === MAX_RETRIES) break;
            console.warn(
              `billing/me attempt ${attempt + 1} failed, retrying in ${RETRY_BACKOFFS[attempt]}ms`,
              err
            );
          }
        }

        // Todos los intentos fallaron
        console.error('Failed to refresh billing state after all retries', lastError);
        set({
          isLoading: false,
          loaded: false,
          error: 'Error al cargar la información de facturación',
        });
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
