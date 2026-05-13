import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Wrench, ChevronDown, ChevronUp, Loader2, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ToolExecutionCardProps {
    toolName: string;
    status: 'running' | 'completed';
    result?: string;
}

const TOOL_LABELS: Record<string, string> = {
    // Shared
    calendar_list_events: 'Consultando calendario',
    calendar_create_event: 'Creando evento',
    calendar_update_event: 'Actualizando evento',
    calendar_delete_event: 'Eliminando evento',
    calendar_check_availability: 'Verificando disponibilidad',
    whatsapp_send_message: 'Enviando WhatsApp',
    whatsapp_send_notification: 'Enviando notificación',
    whatsapp_read_messages: 'Leyendo mensajes',
    // CEO
    delegate_task: 'Delegando tarea',
    check_task_status: 'Consultando estado de tarea',
    list_active_tasks: 'Listando tareas activas',
    // CFO
    get_financial_news: 'Buscando noticias financieras',
    get_stock_data: 'Consultando datos de bolsa',
    get_market_analysis: 'Analizando mercado',
    // CMO
    post_to_linkedin: 'Publicando en LinkedIn',
    post_to_instagram: 'Publicando en Instagram',
    get_social_analytics: 'Consultando analytics',
    schedule_post: 'Programando publicación',
    // CTO
    create_jules_task: 'Enviando tarea a Jules',
    check_jules_status: 'Verificando estado de Jules',
    review_jules_output: 'Revisando código de Jules',
};

export const ToolExecutionCard: React.FC<ToolExecutionCardProps> = ({
    toolName,
    status,
    result,
}) => {
    const [expanded, setExpanded] = useState(false);
    const label = TOOL_LABELS[toolName] || toolName;

    return (
        <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                'my-2 rounded-lg border px-3 py-2 text-xs',
                'bg-surface-elevated/50 border-surface-highlight',
            )}
        >
            <div
                className="flex items-center gap-2 cursor-pointer select-none"
                onClick={() => result && setExpanded(!expanded)}
            >
                {status === 'running' ? (
                    <Loader2 className="h-3.5 w-3.5 text-electric-cyan animate-spin" />
                ) : (
                    <CheckCircle2 className="h-3.5 w-3.5 text-green-400" />
                )}
                <Wrench className="h-3 w-3 text-text-secondary" />
                <span className="text-text-secondary font-medium flex-1">{label}</span>
                {result && (
                    expanded
                        ? <ChevronUp className="h-3 w-3 text-text-muted" />
                        : <ChevronDown className="h-3 w-3 text-text-muted" />
                )}
            </div>
            <AnimatePresence>
                {expanded && result && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <pre className="mt-2 text-[11px] text-text-muted whitespace-pre-wrap break-words max-h-32 overflow-y-auto bg-midnight/60 rounded p-2">
                            {result}
                        </pre>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};
