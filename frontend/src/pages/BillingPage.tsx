import React, { useEffect, useState } from 'react';
import { CreditCard, Zap, Check, Sparkles, ArrowLeft, Loader2, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useBillingStore } from '../store/useBillingStore';
import { authHeaders } from '../services/api';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const PREMIUM_TOPUPS: Array<{ plan_id: string; label: string; price: string }> = [
    { plan_id: 'topup_premium_1k', label: '1.000 msg', price: '€7.99' },
    { plan_id: 'topup_premium_2k', label: '2.000 msg', price: '€14.99' },
    { plan_id: 'topup_premium_10k', label: '10.000 msg', price: '€74.99' },
];

/** Extrae un mensaje de error legible de una respuesta HTTP fallida. */
async function readErrorMessage(response: Response, fallback: string): Promise<string> {
    try {
        const text = await response.text();
        try {
            const json = JSON.parse(text);
            return json?.detail?.message || json?.detail || json?.message || fallback;
        } catch {
            return text || fallback;
        }
    } catch {
        return fallback;
    }
}

/** Skeleton para el estado de carga del panel de facturación */
const BillingSkeleton: React.FC = () => (
    <div data-testid="billing-loading" className="p-6 sm:p-8 w-full max-w-5xl mx-auto animate-pulse">
        <div className="h-9 bg-surface-highlight/50 rounded-lg w-64 mb-8" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
            {[0, 1].map((i) => (
                <div key={i} className="glass-panel p-6 rounded-2xl border border-surface-highlight space-y-4">
                    <div className="h-6 bg-surface-highlight/50 rounded w-40" />
                    <div className="h-10 bg-surface-highlight/50 rounded w-24" />
                    <div className="h-4 bg-surface-highlight/50 rounded w-32" />
                </div>
            ))}
        </div>
    </div>
);

export const BillingPage: React.FC = () => {
    const {
        plan_id,
        status,
        pro_messages_balance,
        topup_messages_balance,
        current_period_end,
        cancel_at_period_end,
        loaded,
        isLoading,
        error,
        stripe_configured,
        refresh,
    } = useBillingStore();

    const [actionError, setActionError] = useState<string | null>(null);
    const [pendingPlan, setPendingPlan] = useState<string | null>(null);
    const [portalLoading, setPortalLoading] = useState(false);

    useEffect(() => {
        refresh();
        // Si volvemos de Stripe (success=true), refrescamos varias veces
        // porque el webhook puede tardar unos segundos en procesar el pago.
        const params = new URLSearchParams(window.location.search);
        if (params.get('success') === 'true') {
            const intervals = [2000, 5000, 10000];
            intervals.forEach((ms) => setTimeout(() => refresh(), ms));
        }
    }, [refresh]);

    const handleCheckout = async (planId: string) => {
        if (pendingPlan) return;
        setActionError(null);
        setPendingPlan(planId);
        try {
            const headers = await authHeaders();
            const response = await fetch(`${API_URL}/billing/checkout`, {
                method: 'POST',
                headers,
                body: JSON.stringify({ plan_id: planId }),
            });
            if (!response.ok) {
                const msg = await readErrorMessage(response, 'No se pudo iniciar el pago. Inténtalo de nuevo.');
                setActionError(msg);
                return;
            }
            const data = await response.json();
            if (data.url) {
                window.location.href = data.url;
            } else {
                setActionError('Respuesta inesperada del servidor de pagos.');
            }
        } catch (err) {
            console.error('Checkout error:', err);
            setActionError('Error de conexión al procesar el pago.');
        } finally {
            setPendingPlan(null);
        }
    };

    const handlePortal = async () => {
        if (portalLoading) return;
        setActionError(null);
        setPortalLoading(true);
        try {
            const headers = await authHeaders();
            const response = await fetch(`${API_URL}/billing/portal`, {
                method: 'POST',
                headers,
            });
            if (!response.ok) {
                const msg = await readErrorMessage(response, 'No se pudo abrir la gestión de suscripción.');
                setActionError(msg);
                return;
            }
            const data = await response.json();
            if (data.url) window.location.href = data.url;
        } catch (err) {
            console.error('Portal error:', err);
            setActionError('Error de conexión al abrir el portal de suscripción.');
        } finally {
            setPortalLoading(false);
        }
    };

    const totalBalance = pro_messages_balance + topup_messages_balance;

    // Loading state: skeleton mientras se obtienen los datos por primera vez
    if (isLoading && !loaded) {
        return <BillingSkeleton />;
    }

    // Error state: mostrar error con botón de reintento
    if (error) {
        return (
            <div className="p-8 w-full max-w-5xl mx-auto flex flex-col items-center justify-center min-h-[50vh] gap-6">
                <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-8 text-center max-w-md">
                    <div className="text-4xl mb-4">⚠️</div>
                    <h2 className="text-xl font-bold text-red-400 mb-2">Error de conexión</h2>
                    <p className="text-text-secondary mb-6">{error}</p>
                    <button
                        onClick={refresh}
                        className="px-6 py-3 bg-electric-cyan/10 text-electric-cyan border border-electric-cyan/30 hover:bg-electric-cyan hover:text-midnight rounded-xl transition-all font-medium"
                    >
                        Reintentar
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-midnight/40 overflow-y-auto">
            {/* Header */}
            <div className="h-14 sm:h-16 pl-14 lg:pl-6 pr-3 sm:pr-6 border-b border-surface flex items-center gap-3 bg-midnight/90 backdrop-blur-md sticky top-0 z-10">
                <Link to="/" className="p-2 hover:bg-surface rounded-full transition-colors text-text-secondary hover:text-text-primary">
                    <ArrowLeft className="h-5 w-5" />
                </Link>
                <h1 className="text-base sm:text-xl font-bold text-text-primary flex items-center gap-2">
                    <CreditCard className="h-5 w-5 text-electric-cyan" />
                    Facturación y Planes
                </h1>
            </div>

            <div className="flex-1 p-4 sm:p-8 w-full max-w-5xl mx-auto">
                {/* Aviso: Stripe no configurado */}
                {!stripe_configured && (
                    <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-4 mb-8 flex items-center gap-3">
                        <span className="text-2xl">⚠️</span>
                        <p className="text-amber-400 text-sm font-medium">
                            Pagos no disponibles temporalmente. El sistema de pagos no está configurado en este momento.
                        </p>
                    </div>
                )}

                {/* Error de acción (checkout/portal) */}
                {actionError && (
                    <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-4 mb-8 flex items-center justify-between gap-3">
                        <p className="text-red-400 text-sm">{actionError}</p>
                        <button onClick={() => setActionError(null)} className="text-red-400/60 hover:text-red-400 text-sm">✕</button>
                    </div>
                )}

                {/* Resumen: Plan actual + Balance */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
                    <div className="glass-panel p-6 rounded-2xl border border-surface-highlight">
                        <div className="flex items-center gap-2 mb-4">
                            <Sparkles className="h-4 w-4 text-luxury-purple" />
                            <h2 className="text-xs uppercase tracking-widest font-mono text-text-secondary">Tu Plan Actual</h2>
                        </div>
                        <p className="text-4xl font-bold capitalize mb-2 text-text-primary">{plan_id}</p>
                        <div className="flex items-center gap-2 mb-1">
                            <span className={`h-2 w-2 rounded-full ${status === 'active' ? 'bg-emerald-500' : 'bg-amber-500'}`} />
                            <p className="text-sm text-text-secondary capitalize">{status}</p>
                        </div>
                        {current_period_end && (
                            <p className="text-text-secondary text-sm mt-1">
                                {cancel_at_period_end ? 'Acceso hasta' : 'Renueva el'}: {new Date(current_period_end).toLocaleDateString()}
                            </p>
                        )}
                        {plan_id !== 'free' && (
                            <button
                                onClick={handlePortal}
                                disabled={portalLoading}
                                className="mt-4 w-full py-2.5 bg-surface-highlight hover:bg-surface-highlight/70 rounded-xl transition-colors font-medium text-text-primary text-sm flex items-center justify-center gap-2 disabled:opacity-60"
                            >
                                {portalLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ExternalLink className="h-4 w-4" />}
                                Gestionar Suscripción
                            </button>
                        )}
                    </div>

                    <div className="glass-panel p-6 rounded-2xl border border-surface-highlight">
                        <div className="flex items-center gap-2 mb-4">
                            <Zap className="h-4 w-4 text-electric-cyan" />
                            <h2 className="text-xs uppercase tracking-widest font-mono text-text-secondary">Balance de Mensajes</h2>
                        </div>
                        <div className="flex flex-col gap-3">
                            <div className="flex justify-between items-baseline">
                                <span className="text-text-secondary text-sm">Mensajes del plan</span>
                                <span className="text-2xl font-bold text-text-primary">{pro_messages_balance}</span>
                            </div>
                            <div className="flex justify-between items-baseline">
                                <span className="text-text-secondary text-sm">Mensajes top-up</span>
                                <span className="text-2xl font-bold text-electric-cyan">{topup_messages_balance}</span>
                            </div>
                            <div className="border-t border-surface-highlight pt-3 flex justify-between items-baseline">
                                <span className="text-text-primary font-medium">Total disponible</span>
                                <span className="text-3xl font-bold text-text-primary">{totalBalance}</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Planes y top-ups: solo si Stripe está configurado */}
                {stripe_configured && (
                    <>
                        <h2 className="text-lg font-bold mb-1 text-text-primary">Planes</h2>
                        <p className="text-xs text-text-secondary mb-6">
                            1 chat con un agente = 1 crédito · 1 reunión de Consejo (board meeting) = 5 créditos.
                        </p>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-12">
                            {/* Free */}
                            <div className="glass-panel p-6 rounded-2xl border border-surface-highlight flex flex-col">
                                <h3 className="text-lg font-bold mb-2 text-text-primary">Free</h3>
                                <p className="text-3xl font-bold mb-4 text-text-primary">€0<span className="text-sm text-text-secondary font-normal">/mes</span></p>
                                <ul className="text-text-secondary text-sm space-y-2 mb-8 flex-1">
                                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-emerald-500" /> 50 créditos/mes</li>
                                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-emerald-500" /> ≈ 10 reuniones de Consejo</li>
                                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-emerald-500" /> 20 MB RAG</li>
                                    <li className="flex items-center gap-2 opacity-50">Sin agentes custom</li>
                                </ul>
                                <button disabled className="w-full py-2.5 bg-surface-highlight/40 text-text-secondary rounded-xl cursor-not-allowed text-sm">
                                    {plan_id === 'free' ? 'Plan Actual' : 'Tier base'}
                                </button>
                            </div>

                            {/* Starter */}
                            <div className="glass-panel p-6 rounded-2xl border border-surface-highlight flex flex-col">
                                <h3 className="text-lg font-bold mb-2 text-text-primary">Starter</h3>
                                <p className="text-3xl font-bold mb-4 text-text-primary">€9.99<span className="text-sm text-text-secondary font-normal">/mes</span></p>
                                <ul className="text-text-secondary text-sm space-y-2 mb-8 flex-1">
                                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-emerald-500" /> 600 créditos/mes</li>
                                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-emerald-500" /> 100 MB RAG</li>
                                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-emerald-500" /> 3 Agentes Custom</li>
                                </ul>
                                <button
                                    onClick={() => handleCheckout('starter')}
                                    disabled={plan_id === 'starter' || pendingPlan === 'starter'}
                                    className="w-full py-2.5 bg-electric-cyan/10 text-electric-cyan border border-electric-cyan/30 hover:bg-electric-cyan hover:text-midnight disabled:opacity-50 disabled:cursor-not-allowed rounded-xl transition-all font-medium text-sm flex items-center justify-center gap-2"
                                >
                                    {pendingPlan === 'starter' && <Loader2 className="h-4 w-4 animate-spin" />}
                                    {plan_id === 'starter' ? 'Plan Actual' : 'Suscribirse'}
                                </button>
                            </div>

                            {/* Premium */}
                            <div className="glass-panel p-6 rounded-2xl border border-luxury-purple/50 flex flex-col relative overflow-hidden">
                                <div className="absolute top-0 right-0 bg-luxury-purple text-white text-[10px] font-bold px-3 py-1 rounded-bl-lg tracking-wide">RECOMENDADO</div>
                                <h3 className="text-lg font-bold mb-2 text-text-primary">Premium</h3>
                                <p className="text-3xl font-bold mb-4 text-text-primary">€19.99<span className="text-sm text-text-secondary font-normal">/mes</span></p>
                                <ul className="text-text-secondary text-sm space-y-2 mb-8 flex-1">
                                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-luxury-purple" /> 1.500 créditos/mes</li>
                                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-luxury-purple" /> 1 GB RAG</li>
                                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-luxury-purple" /> Agentes Custom Ilimitados</li>
                                    <li className="flex items-center gap-2"><Check className="h-4 w-4 text-luxury-purple" /> API Access</li>
                                </ul>
                                <button
                                    onClick={() => handleCheckout('premium')}
                                    disabled={plan_id === 'premium' || pendingPlan === 'premium'}
                                    className="w-full py-2.5 bg-luxury-purple text-white hover:bg-luxury-purple/80 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl transition-all font-medium text-sm flex items-center justify-center gap-2"
                                >
                                    {pendingPlan === 'premium' && <Loader2 className="h-4 w-4 animate-spin" />}
                                    {plan_id === 'premium' ? 'Plan Actual' : 'Suscribirse'}
                                </button>
                            </div>
                        </div>

                        <h2 className="text-lg font-bold mb-2 text-text-primary">Packs adicionales (top-ups)</h2>
                        <p className="text-sm text-text-secondary mb-6">Mensajes extra que no caducan mientras tu cuenta esté activa.</p>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                            <div className="glass-panel p-6 rounded-2xl border border-surface-highlight">
                                <h3 className="text-base font-bold mb-1 text-text-primary">Free</h3>
                                <p className="text-xs text-text-secondary mb-3">Disponible en cualquier plan</p>
                                <button
                                    onClick={() => handleCheckout('topup_free')}
                                    disabled={pendingPlan === 'topup_free'}
                                    className="w-full px-3 py-2.5 bg-surface-highlight hover:bg-surface-highlight/70 disabled:opacity-50 rounded-xl text-sm flex justify-between items-center text-text-primary transition-colors"
                                >
                                    <span>100 msg</span><span className="font-bold">€4.99</span>
                                </button>
                            </div>

                            <div className="glass-panel p-6 rounded-2xl border border-surface-highlight">
                                <h3 className="text-base font-bold mb-1 text-text-primary">Starter</h3>
                                <p className="text-xs text-text-secondary mb-3">Requiere plan Starter o Premium</p>
                                <button
                                    onClick={() => handleCheckout('topup_starter')}
                                    disabled={plan_id === 'free' || pendingPlan === 'topup_starter'}
                                    className="w-full px-3 py-2.5 bg-surface-highlight hover:bg-surface-highlight/70 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm flex justify-between items-center text-text-primary transition-colors"
                                >
                                    <span>700 msg</span><span className="font-bold">€5.99</span>
                                </button>
                            </div>

                            <div className="glass-panel p-6 rounded-2xl border border-luxury-purple/40">
                                <h3 className="text-base font-bold mb-1 text-text-primary">Premium</h3>
                                <p className="text-xs text-text-secondary mb-3">Requiere plan Premium</p>
                                <div className="space-y-2">
                                    {PREMIUM_TOPUPS.map((t) => (
                                        <button
                                            key={t.plan_id}
                                            onClick={() => handleCheckout(t.plan_id)}
                                            disabled={plan_id !== 'premium' || pendingPlan === t.plan_id}
                                            className="w-full px-3 py-2.5 bg-surface-highlight hover:bg-surface-highlight/70 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm flex justify-between items-center text-text-primary transition-colors"
                                        >
                                            <span>{t.label}</span><span className="font-bold">{t.price}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};
