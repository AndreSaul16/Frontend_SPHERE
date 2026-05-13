/**
 * Sección Storage: muestra uso de tokens (budget diario) y el progreso de
 * cuota de GridFS. Solo lectura.
 */
import { useEffect, useState } from "react";
import { HardDrive, Zap, RefreshCw } from "lucide-react";
import { profileService, type UserProfile } from "@/services/api";

export function StorageSettings() {
  const [usage, setUsage] = useState<UserProfile["usage"] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setUsage(await profileService.getUsage());
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (loading && !usage)
    return <p className="text-text-secondary">Cargando...</p>;

  const budget = usage?.token_budget_daily || 100_000;
  const used = usage?.tokens_used_today || 0;
  const pct = Math.min(100, (used / budget) * 100);
  const resetsAt = usage?.tokens_reset_at
    ? new Date(usage.tokens_reset_at).toLocaleString()
    : "00:00 UTC del día siguiente";

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      <section className="p-5 rounded-2xl bg-surface/30 border border-surface-highlight space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-text-primary font-semibold">
            <Zap className="h-5 w-5 text-electric-cyan" />
            <h3>Uso de tokens (hoy)</h3>
          </div>
          <button
            onClick={load}
            className="p-2 text-text-secondary hover:text-electric-cyan transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-2">
          <div className="flex items-end justify-between text-sm">
            <span className="text-text-primary font-mono">
              {used.toLocaleString()} / {budget.toLocaleString()}
            </span>
            <span className="text-text-secondary text-xs">
              {pct.toFixed(1)}%
            </span>
          </div>
          <div className="h-3 bg-midnight/50 rounded-full overflow-hidden border border-surface-highlight">
            <div
              className={`h-full rounded-full transition-all ${
                pct >= 90
                  ? "bg-red-500"
                  : pct >= 70
                  ? "bg-amber-500"
                  : "bg-electric-cyan"
              }`}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>

        <p className="text-xs text-text-secondary">
          El presupuesto se resetea diariamente. Próximo reset: {resetsAt}.
        </p>
      </section>

      <section className="p-5 rounded-2xl bg-surface/30 border border-surface-highlight space-y-3">
        <div className="flex items-center gap-3 text-text-primary font-semibold">
          <HardDrive className="h-5 w-5 text-luxury-purple" />
          <h3>Almacenamiento de documentos</h3>
        </div>
        <p className="text-xs text-text-secondary">
          Los documentos que subes a tus agentes se almacenan de forma privada
          en GridFS y se vectorizan para que los agentes puedan usarlos en sus
          respuestas. Cada usuario tiene una cuota de 500 MB por defecto.
        </p>
        <div className="p-3 rounded-xl bg-midnight/40 border border-surface-highlight text-xs font-mono text-text-secondary">
          Uso real por usuario: disponible en endpoint del backend (integrar en
          próxima versión).
        </div>
      </section>
    </div>
  );
}
