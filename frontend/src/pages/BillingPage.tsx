import React, { useEffect } from 'react';
import { useBillingStore } from '../store/useBillingStore';

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
        // sin auth
    }
    return headers;
}

const PREMIUM_TOPUPS: Array<{ plan_id: string; label: string; price: string }> = [
    { plan_id: 'topup_premium_1k', label: '1.000 msg', price: '€7.99' },
    { plan_id: 'topup_premium_2k', label: '2.000 msg', price: '€14.99' },
    { plan_id: 'topup_premium_10k', label: '10.000 msg', price: '€74.99' },
];

export const BillingPage: React.FC = () => {
    const {
        plan_id,
        status,
        pro_messages_balance,
        topup_messages_balance,
        current_period_end,
        cancel_at_period_end,
        refresh,
    } = useBillingStore();

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
        try {
            const headers = await authHeaders();
            const response = await fetch(`${API_URL}/billing/checkout`, {
                method: 'POST',
                headers,
                body: JSON.stringify({ plan_id: planId }),
            });
            if (!response.ok) {
                const text = await response.text();
                console.error('Checkout error', response.status, text);
                return;
            }
            const data = await response.json();
            if (data.url) window.location.href = data.url;
        } catch (error) {
            console.error('Checkout error:', error);
        }
    };

    const handlePortal = async () => {
        try {
            const headers = await authHeaders();
            const response = await fetch(`${API_URL}/billing/portal`, {
                method: 'POST',
                headers,
            });
            if (!response.ok) {
                console.error('Portal error', response.status);
                return;
            }
            const data = await response.json();
            if (data.url) window.location.href = data.url;
        } catch (error) {
            console.error('Portal error:', error);
        }
    };

    const totalBalance = pro_messages_balance + topup_messages_balance;

    return (
        <div className="p-8 text-white w-full max-w-5xl mx-auto">
            <h1 className="text-3xl font-bold mb-8">Facturación y Planes</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <h2 className="text-xl font-semibold mb-4 text-indigo-400">Tu Plan Actual</h2>
                    <p className="text-4xl font-bold capitalize mb-2">{plan_id}</p>
                    <p className="text-sm text-slate-400 mb-2">Estado: <span className="capitalize">{status}</span></p>
                    {current_period_end && (
                        <p className="text-slate-400 mb-1">
                            {cancel_at_period_end ? 'Acceso hasta' : 'Renueva el'}: {new Date(current_period_end).toLocaleDateString()}
                        </p>
                    )}
                    {plan_id !== 'free' && (
                        <button
                            onClick={handlePortal}
                            className="mt-4 w-full py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors font-medium"
                        >
                            Gestionar Suscripción
                        </button>
                    )}
                </div>

                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <h2 className="text-xl font-semibold mb-4 text-emerald-400">Balance de Mensajes Pro</h2>
                    <div className="flex flex-col gap-2 mb-4">
                        <div className="flex justify-between items-center">
                            <span className="text-slate-300">Mensajes del plan:</span>
                            <span className="text-2xl font-bold">{pro_messages_balance}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-slate-300">Mensajes top-up:</span>
                            <span className="text-2xl font-bold text-emerald-400">{topup_messages_balance}</span>
                        </div>
                        <div className="border-t border-slate-700 pt-2 flex justify-between items-center">
                            <span className="text-slate-300">Total disponible:</span>
                            <span className="text-2xl font-bold">{totalBalance}</span>
                        </div>
                    </div>
                </div>
            </div>

            <h2 className="text-2xl font-bold mb-6">Planes</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700 flex flex-col">
                    <h3 className="text-lg font-bold mb-2">Free</h3>
                    <p className="text-3xl font-bold mb-4">€0<span className="text-sm text-slate-400 font-normal">/mes</span></p>
                    <ul className="text-slate-300 space-y-2 mb-8 flex-1">
                        <li>5 Mensajes Pro</li>
                        <li>20 MB RAG</li>
                        <li>Sin agentes custom</li>
                    </ul>
                    <button
                        disabled
                        className="w-full py-2 bg-slate-700/50 text-slate-400 rounded-lg cursor-not-allowed"
                    >
                        {plan_id === 'free' ? 'Plan Actual' : 'Tier base'}
                    </button>
                </div>

                <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700 flex flex-col">
                    <h3 className="text-lg font-bold mb-2">Starter</h3>
                    <p className="text-3xl font-bold mb-4">€9.99<span className="text-sm text-slate-400 font-normal">/mes</span></p>
                    <ul className="text-slate-300 space-y-2 mb-8 flex-1">
                        <li>1.000 Mensajes Pro</li>
                        <li>100 MB RAG</li>
                        <li>3 Agentes Custom</li>
                    </ul>
                    <button
                        onClick={() => handleCheckout('starter')}
                        disabled={plan_id === 'starter'}
                        className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors font-medium"
                    >
                        {plan_id === 'starter' ? 'Plan Actual' : 'Suscribirse'}
                    </button>
                </div>

                <div className="bg-slate-800 p-6 rounded-xl border border-indigo-500 flex flex-col relative overflow-hidden">
                    <div className="absolute top-0 right-0 bg-indigo-500 text-xs font-bold px-3 py-1 rounded-bl-lg">RECOMENDADO</div>
                    <h3 className="text-lg font-bold mb-2">Premium</h3>
                    <p className="text-3xl font-bold mb-4">€19.99<span className="text-sm text-slate-400 font-normal">/mes</span></p>
                    <ul className="text-slate-300 space-y-2 mb-8 flex-1">
                        <li>2.000 Mensajes Pro</li>
                        <li>1 GB RAG</li>
                        <li>Agentes Custom Ilimitados</li>
                        <li>API Access</li>
                    </ul>
                    <button
                        onClick={() => handleCheckout('premium')}
                        disabled={plan_id === 'premium'}
                        className="w-full py-2 bg-indigo-500 hover:bg-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg transition-colors font-medium"
                    >
                        {plan_id === 'premium' ? 'Plan Actual' : 'Suscribirse'}
                    </button>
                </div>
            </div>

            <h2 className="text-2xl font-bold mb-6">Packs adicionales (top-ups)</h2>
            <p className="text-sm text-slate-400 mb-6">Mensajes extra que no caducan mientras tu cuenta esté activa.</p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700">
                    <h3 className="text-lg font-bold mb-1">Free</h3>
                    <p className="text-xs text-slate-500 mb-3">Disponible en cualquier plan</p>
                    <button
                        onClick={() => handleCheckout('topup_free')}
                        className="w-full px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded text-sm flex justify-between items-center"
                    >
                        <span>100 msg</span><span className="font-bold">€4.99</span>
                    </button>
                </div>

                <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700">
                    <h3 className="text-lg font-bold mb-1">Starter</h3>
                    <p className="text-xs text-slate-500 mb-3">Requiere plan Starter o Premium</p>
                    <button
                        onClick={() => handleCheckout('topup_starter')}
                        disabled={plan_id === 'free'}
                        className="w-full px-3 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm flex justify-between items-center"
                    >
                        <span>700 msg</span><span className="font-bold">€5.99</span>
                    </button>
                </div>

                <div className="bg-slate-800/50 p-6 rounded-xl border border-indigo-500/40">
                    <h3 className="text-lg font-bold mb-1">Premium</h3>
                    <p className="text-xs text-slate-500 mb-3">Requiere plan Premium</p>
                    <div className="space-y-2">
                        {PREMIUM_TOPUPS.map((t) => (
                            <button
                                key={t.plan_id}
                                onClick={() => handleCheckout(t.plan_id)}
                                disabled={plan_id !== 'premium'}
                                className="w-full px-3 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm flex justify-between items-center"
                            >
                                <span>{t.label}</span><span className="font-bold">{t.price}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};
