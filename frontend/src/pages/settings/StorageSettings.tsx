/**
 * Sección Uso & Storage: muestra el uso de tokens (budget diario) y el uso real
 * de almacenamiento de documentos (GridFS) por usuario, con la cuota de su plan.
 * Solo lectura.
 */
import { useEffect, useState } from "react";
import { HardDrive, Zap, RefreshCw, FileText } from "lucide-react";
import { profileService, type UserProfile, type StorageUsage } from "@/services/api";

function formatBytes(bytes: number): string {
  if (!bytes || bytes < 1024) return `${bytes || 0} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let value = bytes / 1024;
  let i = 0;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i++;
  }
  return `${value.toFixed(value < 10 ? 1 : 0)} ${units[i]}`;
}

function barColor(pct: number): string {
  if (pct >= 90) return "bg-red-500";
  if (pct >= 70) return "bg-amber-500";
  return "bg-electric-cyan";
}

export function StorageSettings() {
  const [usage, setUsage] = useState<UserProfile["usage"] | null>(null);
  const [storage, setStorage] = useState<StorageUsage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [u, s] = await Promise.all([
        profileService.getUsage(),
        profileService.getStorage().catch(() => null), // tolerar si el endpoint falla
      ]);
      setUsage(u);
      setStorage(s);
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

  const storagePct = storage?.percent_used ?? 0;
  const planLabel: Record<string, string> = { free: "Free", starter: "Starter", premium: "Premium" };

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={load} className="text-red-400/70 hover:text-red-400 underline">Reintentar</button>
        </div>
      )}

      {/* Uso de tokens (hoy) */}
      <section className="glass-panel p-5 rounded-2xl border border-surface-highlight space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 text-text-primary font-semibold">
            <div className="h-9 w-9 rounded-xl bg-electric-cyan/10 flex items-center justify-center">
              <Zap className="h-5 w-5 text-electric-cyan" />
            </div>
            <div>
              <h3 className="text-sm">Uso de tokens</h3>
              <p className="text-[11px] text-text-secondary font-normal">Presupuesto diario</p>
            </div>
          </div>
          <button
            onClick={load}
            className="p-2 text-text-secondary hover:text-electric-cyan transition-colors"
            title="Actualizar"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>

        <div className="space-y-2">
          <div className="flex items-end justify-between text-sm">
            <span className="text-text-primary font-mono">
              {used.toLocaleString()} <span className="text-text-secondary">/ {budget.toLocaleString()} tokens</span>
            </span>
            <span className="text-text-secondary text-xs font-mono">{pct.toFixed(1)}%</span>
          </div>
          <div className="h-2.5 bg-midnight/50 rounded-full overflow-hidden border border-surface-highlight">
            <div className={`h-full rounded-full transition-all ${barColor(pct)}`} style={{ width: `${pct}%` }} />
          </div>
          <p className="text-[11px] text-text-secondary">Próximo reset: {resetsAt}.</p>
        </div>
      </section>

      {/* Almacenamiento de documentos (GridFS) */}
      <section className="glass-panel p-5 rounded-2xl border border-surface-highlight space-y-4">
        <div className="flex items-center gap-3 text-text-primary font-semibold">
          <div className="h-9 w-9 rounded-xl bg-luxury-purple/10 flex items-center justify-center">
            <HardDrive className="h-5 w-5 text-luxury-purple" />
          </div>
          <div>
            <h3 className="text-sm">Almacenamiento de documentos</h3>
            <p className="text-[11px] text-text-secondary font-normal">
              Plan {storage ? planLabel[storage.plan_id] || storage.plan_id : "—"}
            </p>
          </div>
        </div>

        {storage ? (
          <>
            <div className="space-y-2">
              <div className="flex items-end justify-between text-sm">
                <span className="text-text-primary font-mono">
                  {formatBytes(storage.used_bytes)} <span className="text-text-secondary">/ {formatBytes(storage.quota_bytes)}</span>
                </span>
                <span className="text-text-secondary text-xs font-mono">{storagePct.toFixed(1)}%</span>
              </div>
              <div className="h-2.5 bg-midnight/50 rounded-full overflow-hidden border border-surface-highlight">
                <div className={`h-full rounded-full transition-all ${barColor(storagePct)}`} style={{ width: `${storagePct}%` }} />
              </div>
            </div>
            <div className="flex items-center gap-2 text-[11px] text-text-secondary">
              <FileText className="h-3.5 w-3.5" />
              {storage.file_count} {storage.file_count === 1 ? "documento" : "documentos"} en tus agentes
            </div>
          </>
        ) : (
          <p className="text-xs text-text-secondary">
            No se pudo obtener el uso de almacenamiento en este momento.
          </p>
        )}
        <p className="text-[11px] text-text-secondary leading-relaxed">
          Los documentos que subes a tus agentes se almacenan de forma privada y se
          vectorizan para que los agentes puedan usarlos en sus respuestas.
        </p>
      </section>
    </div>
  );
}
