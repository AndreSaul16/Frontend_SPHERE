import { motion, AnimatePresence } from 'framer-motion';
import { Users, Zap, Swords, X } from 'lucide-react';
import { useBillingStore } from '@/store/useBillingStore';

interface Props {
    open: boolean;
    loading?: boolean;
    onActivate: (devil: boolean) => void;   // activa el debate (PATCH) y crea sesión
    onRouterOnly: () => void;                // crea sesión sin debate (solo router)
    onClose: () => void;
}

/**
 * Modal de 1 clic para activar el Board Meeting al crear una Junta Directiva.
 * Muestra el coste real y el saldo, y permite activar el Abogado del Diablo.
 * Elimina la fricción de tener que ir a Configuración a activar el servicio estrella.
 */
export function BoardActivationModal({ open, loading, onActivate, onRouterOnly, onClose }: Props) {
    const { pro_messages_balance, topup_messages_balance } = useBillingStore();
    const balance = pro_messages_balance + topup_messages_balance;

    return (
        <AnimatePresence>
            {open && (
                <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="w-full max-w-md bg-surface border border-white/10 rounded-3xl p-7 shadow-2xl relative overflow-hidden"
                    >
                        {/* glow */}
                        <div className="absolute -top-20 -right-20 h-48 w-48 bg-electric-cyan/10 blur-3xl rounded-full pointer-events-none" />

                        <button onClick={onClose} className="absolute top-4 right-4 p-1.5 rounded-lg text-gray-500 hover:text-white hover:bg-white/10 transition-colors">
                            <X className="h-4 w-4" />
                        </button>

                        <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-electric-cyan/20 to-luxury-purple/20 border border-white/10 flex items-center justify-center mb-4">
                            <Users className="h-7 w-7 text-electric-cyan" />
                        </div>

                        <h2 className="text-xl font-bold text-white mb-2">¿Activar el debate de la junta?</h2>
                        <p className="text-sm text-gray-400 leading-relaxed mb-5">
                            En modo debate, tus directores <strong className="text-white">discuten en paralelo</strong>, se
                            rebaten, votan y el CEO cierra con un <strong className="text-white">acta de decisión</strong>.
                            Sin debate, un único orquestador delega al experto más adecuado.
                        </p>

                        <div className="flex items-center justify-between p-3 rounded-2xl bg-midnight/40 border border-white/5 mb-5">
                            <span className="flex items-center gap-2 text-sm text-gray-300">
                                <Zap className="h-4 w-4 text-electric-cyan" />
                                Cada debate cuesta hasta <strong className="text-white">5&nbsp;⚡</strong>
                                <span className="text-gray-500">(3 si el triage reduce la junta)</span>
                            </span>
                            <span className="text-xs font-mono text-gray-500 whitespace-nowrap">tienes {balance} ⚡</span>
                        </div>

                        <div className="space-y-2.5">
                            <button
                                onClick={() => onActivate(false)}
                                disabled={loading}
                                className="w-full py-3 rounded-2xl bg-electric-cyan text-midnight font-semibold hover:scale-[1.02] transition-transform shadow-[0_0_24px_rgba(0,245,212,0.3)] disabled:opacity-50"
                            >
                                Activar debate
                            </button>
                            <button
                                onClick={() => onActivate(true)}
                                disabled={loading}
                                className="w-full py-3 rounded-2xl bg-rose-500/10 text-rose-300 border border-rose-500/30 font-medium hover:bg-rose-500/20 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                            >
                                <Swords className="h-4 w-4" />
                                Activar con Abogado del Diablo
                            </button>
                            <button
                                onClick={onRouterOnly}
                                disabled={loading}
                                className="w-full py-2.5 rounded-2xl text-gray-400 hover:text-white text-sm transition-colors disabled:opacity-50"
                            >
                                Solo router (1 ⚡ por mensaje, sin debate)
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
