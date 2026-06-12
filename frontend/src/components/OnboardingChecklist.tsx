/**
 * Onboarding first-run: checklist de 3 pasos sobre el Welcome Screen.
 * El progreso se deriva de datos reales (sesiones de grupo, mensajes, agentes custom)
 * — sin estado nuevo en backend. Al completar los 3 pasos llama a completeOnboarding()
 * y deja de mostrarse (flag onboarding_completed del perfil).
 */
import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Check, Users, MessagesSquare, Sparkles } from "lucide-react";
import { useChatStore } from "@/store/useChatStore";
import { profileService } from "@/services/api";
import { cn } from "@/lib/utils";

interface Props {
    onPrimaryAction: () => void; // abre el selector de agentes (paso 1)
}

export function OnboardingChecklist({ onPrimaryAction }: Props) {
    const { sessions, customAgents, messagesBySession } = useChatStore();
    const [dismissed, setDismissed] = useState(false);
    const [loaded, setLoaded] = useState(false);
    const completedRef = useState({ done: false })[0];

    // Cargar flag de perfil: si ya completó onboarding, no mostrar.
    useEffect(() => {
        let alive = true;
        profileService.getProfile()
            .then((p) => { if (alive && p.onboarding_completed) setDismissed(true); })
            .catch(() => { /* ignore */ })
            .finally(() => { if (alive) setLoaded(true); });
        return () => { alive = false; };
    }, []);

    const steps = useMemo(() => {
        const hasGroup = sessions.some((s) => s.type === "group");
        const hasMessage = Object.values(messagesBySession).some((msgs) =>
            msgs.some((m) => m.role === "user")
        );
        const hasCustom = customAgents.length > 0;
        return [
            { key: "group", label: "Convoca tu Junta Directiva", desc: "Crea un chat grupal con tus expertos", done: hasGroup, icon: Users },
            { key: "debate", label: "Lanza tu primer debate", desc: "Envía una decisión y deja que debatan", done: hasMessage, icon: MessagesSquare },
            { key: "custom", label: "Crea tu experto a medida", desc: "Un agente con tu conocimiento y tono", done: hasCustom, icon: Sparkles },
        ];
    }, [sessions, customAgents, messagesBySession]);

    const allDone = steps.every((s) => s.done);

    // Al completar los 3, marcar onboarding como completado (una vez).
    useEffect(() => {
        if (allDone && loaded && !dismissed && !completedRef.done) {
            completedRef.done = true;
            profileService.completeOnboarding().catch(() => { /* ignore */ });
        }
    }, [allDone, loaded, dismissed, completedRef]);

    if (dismissed || allDone) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full rounded-2xl bg-white/[0.02] border border-white/10 p-4 space-y-2.5 text-left"
        >
            <div className="flex items-center justify-between">
                <p className="text-[10px] font-mono uppercase tracking-widest text-electric-cyan">Primeros pasos</p>
                <span className="text-[10px] font-mono text-gray-500">
                    {steps.filter((s) => s.done).length}/{steps.length}
                </span>
            </div>
            {steps.map((step) => {
                const Icon = step.icon;
                return (
                    <button
                        key={step.key}
                        onClick={step.done ? undefined : onPrimaryAction}
                        disabled={step.done}
                        className={cn(
                            "w-full flex items-center gap-3 p-2.5 rounded-xl border transition-all text-left",
                            step.done
                                ? "border-emerald-500/20 bg-emerald-500/[0.04] cursor-default"
                                : "border-white/5 hover:border-electric-cyan/30 hover:bg-white/[0.03]"
                        )}
                    >
                        <div className={cn(
                            "h-7 w-7 rounded-lg flex items-center justify-center shrink-0",
                            step.done ? "bg-emerald-500/20 text-emerald-400" : "bg-white/5 text-gray-400"
                        )}>
                            {step.done ? <Check className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
                        </div>
                        <div className="min-w-0">
                            <p className={cn("text-xs font-semibold", step.done ? "text-gray-400 line-through" : "text-white")}>
                                {step.label}
                            </p>
                            <p className="text-[10px] text-gray-500 truncate">{step.desc}</p>
                        </div>
                    </button>
                );
            })}
        </motion.div>
    );
}
