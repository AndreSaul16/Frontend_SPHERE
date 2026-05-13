/**
 * Barra compacta de uso de tokens diarios. Se muestra en el header/sidebar
 * para dar visibilidad del presupuesto sin navegar a Settings → Storage.
 */
import { useEffect, useState } from "react";
import { Zap } from "lucide-react";
import { profileService, type UserProfile } from "@/services/api";

interface Props {
  className?: string;
  refreshMs?: number;
}

export function TokenUsageBar({ className = "", refreshMs = 60_000 }: Props) {
  const [usage, setUsage] = useState<UserProfile["usage"] | null>(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const u = await profileService.getUsage();
        if (active) setUsage(u);
      } catch {
        /* silencioso */
      }
    };
    load();
    const interval = setInterval(load, refreshMs);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [refreshMs]);

  if (!usage) return null;

  const budget = usage.token_budget_daily || 100_000;
  const used = usage.tokens_used_today || 0;
  const pct = Math.min(100, (used / budget) * 100);
  const color =
    pct >= 90 ? "bg-red-500" : pct >= 70 ? "bg-amber-500" : "bg-electric-cyan";

  return (
    <div
      className={`flex items-center gap-2 px-3 py-1.5 bg-surface/40 border border-surface-highlight rounded-xl ${className}`}
      title={`${used.toLocaleString()} / ${budget.toLocaleString()} tokens hoy`}
    >
      <Zap className="h-3.5 w-3.5 text-electric-cyan shrink-0" />
      <div className="flex-1 min-w-[60px] max-w-[140px]">
        <div className="h-1.5 bg-midnight/60 rounded-full overflow-hidden">
          <div
            className={`h-full ${color} transition-all`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
      <span className="text-[10px] font-mono text-text-secondary whitespace-nowrap">
        {pct.toFixed(0)}%
      </span>
    </div>
  );
}
