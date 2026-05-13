/**
 * Modal para confirmar acciones destructivas de tools (post a LinkedIn/Instagram,
 * envío de mensajes, etc.). El backend devuelve un error estructurado
 * `{error: "confirmation_required", tool, action_summary}` que el agente reporta;
 * este modal muestra la visualización y deja al usuario confirmar/cancelar.
 *
 * Uso: renderizar en el árbol principal y controlar apertura desde el
 * componente que detecta el evento de confirmation_required.
 */
import { AlertTriangle, X, Check } from "lucide-react";

export interface PendingConfirmation {
  tool: string;
  action_summary: string;
  args?: Record<string, any>;
  onConfirm: () => void | Promise<void>;
  onCancel?: () => void;
}

interface Props {
  pending: PendingConfirmation | null;
  onClose: () => void;
}

export function ToolConfirmationModal({ pending, onClose }: Props) {
  if (!pending) return null;

  const handleCancel = () => {
    pending.onCancel?.();
    onClose();
  };

  const handleConfirm = async () => {
    await pending.onConfirm();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-surface border border-surface-highlight rounded-2xl w-full max-w-lg shadow-2xl">
        <div className="flex items-start gap-3 p-5 border-b border-surface-highlight">
          <div className="p-2 bg-amber-500/10 rounded-xl">
            <AlertTriangle className="h-5 w-5 text-amber-400" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-text-primary font-semibold">Confirmar acción</h3>
            <p className="text-xs text-text-secondary font-mono mt-1">
              {pending.tool}
            </p>
          </div>
          <button
            onClick={handleCancel}
            className="p-1.5 text-text-secondary hover:text-text-primary rounded-lg hover:bg-midnight/50 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="p-5 space-y-3">
          <p className="text-sm text-text-primary leading-relaxed">
            {pending.action_summary}
          </p>
          {pending.args && Object.keys(pending.args).length > 0 && (
            <details className="text-xs">
              <summary className="cursor-pointer text-text-secondary hover:text-text-primary">
                Ver parámetros completos
              </summary>
              <pre className="mt-2 p-3 bg-midnight/50 border border-surface-highlight rounded-xl overflow-x-auto text-[11px] text-text-secondary">
                {JSON.stringify(pending.args, null, 2)}
              </pre>
            </details>
          )}
        </div>

        <div className="flex items-center justify-end gap-2 p-5 border-t border-surface-highlight">
          <button
            onClick={handleCancel}
            className="px-4 py-2 bg-midnight/50 text-text-secondary border border-surface-highlight rounded-xl hover:text-text-primary transition-colors text-sm"
          >
            Cancelar
          </button>
          <button
            onClick={handleConfirm}
            className="flex items-center gap-2 px-4 py-2 bg-electric-cyan/10 text-electric-cyan border border-electric-cyan/30 rounded-xl hover:bg-electric-cyan hover:text-midnight transition-all text-sm font-medium"
          >
            <Check className="h-4 w-4" />
            Confirmar
          </button>
        </div>
      </div>
    </div>
  );
}
