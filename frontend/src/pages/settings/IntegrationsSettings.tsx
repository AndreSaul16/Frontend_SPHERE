/**
 * Sección Integraciones: conectar/desconectar GitHub, Notion, Slack vía OAuth.
 */
import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { Github, FileText, Slack as SlackIcon, Link2, Unlink, CheckCircle2 } from "lucide-react";
import { integrationsService, type IntegrationsList } from "@/services/api";

const PROVIDER_META: Record<
  string,
  { label: string; icon: React.ReactNode; description: string }
> = {
  github: {
    label: "GitHub",
    icon: <Github className="h-6 w-6" />,
    description: "Permite al CTO crear repos, issues y PRs en tu cuenta.",
  },
  notion: {
    label: "Notion",
    icon: <FileText className="h-6 w-6" />,
    description: "Permite a los agentes crear y actualizar páginas en tu workspace.",
  },
  slack: {
    label: "Slack",
    icon: <SlackIcon className="h-6 w-6" />,
    description: "Permite enviar mensajes a canales autorizados.",
  },
};

export function IntegrationsSettings() {
  const [data, setData] = useState<IntegrationsList | null>(null);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [params, setParams] = useSearchParams();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await integrationsService.list());
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Banner cuando volvemos del callback OAuth
  const justConnected = params.get("connected");
  useEffect(() => {
    if (justConnected) {
      const t = setTimeout(() => {
        params.delete("connected");
        setParams(params, { replace: true });
      }, 5000);
      return () => clearTimeout(t);
    }
  }, [justConnected, params, setParams]);

  const handleConnect = async (provider: string) => {
    setWorking(provider);
    setError(null);
    try {
      await integrationsService.connect(provider);
      // El flujo redirige al provider; si no, recargamos
    } catch (e) {
      setError(String(e));
      setWorking(null);
    }
  };

  const handleDisconnect = async (provider: string) => {
    setWorking(provider);
    setError(null);
    try {
      await integrationsService.disconnect(provider);
      await load();
    } catch (e) {
      setError(String(e));
    } finally {
      setWorking(null);
    }
  };

  if (loading && !data) return <p className="text-text-secondary">Cargando...</p>;

  return (
    <div className="space-y-6">
      {justConnected && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
          <CheckCircle2 className="h-4 w-4" />
          Conectado correctamente a {justConnected}
        </div>
      )}

      {error && (
        <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
          {error}
        </div>
      )}

      <p className="text-sm text-text-secondary">
        Conecta tus servicios externos. Los tokens se cifran en reposo y se usan
        cuando los agentes ejecutan acciones en tu nombre.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {(data?.available || Object.keys(PROVIDER_META)).map((p) => {
          const meta = PROVIDER_META[p] || {
            label: p,
            icon: <Link2 className="h-6 w-6" />,
            description: "",
          };
          const isConnected = data?.status?.[p] ?? false;
          const isWorking = working === p;

          return (
            <div
              key={p}
              className="p-5 rounded-2xl bg-surface/30 border border-surface-highlight space-y-3"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3 text-text-primary">
                  {meta.icon}
                  <div>
                    <h3 className="font-semibold">{meta.label}</h3>
                    <p className="text-xs text-text-secondary mt-1">
                      {meta.description}
                    </p>
                  </div>
                </div>
                {isConnected && (
                  <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full text-[10px]">
                    Conectado
                  </span>
                )}
              </div>

              {isConnected ? (
                <button
                  onClick={() => handleDisconnect(p)}
                  disabled={isWorking}
                  className="w-full flex items-center justify-center gap-2 py-2 bg-red-500/10 text-red-400 border border-red-500/20 rounded-xl hover:bg-red-500 hover:text-white transition-all text-sm font-medium disabled:opacity-50"
                >
                  <Unlink className="h-4 w-4" />
                  {isWorking ? "Desconectando..." : "Desconectar"}
                </button>
              ) : (
                <button
                  onClick={() => handleConnect(p)}
                  disabled={isWorking}
                  className="w-full flex items-center justify-center gap-2 py-2 bg-electric-cyan/10 text-electric-cyan border border-electric-cyan/30 rounded-xl hover:bg-electric-cyan hover:text-midnight transition-all text-sm font-medium disabled:opacity-50"
                >
                  <Link2 className="h-4 w-4" />
                  {isWorking ? "Conectando..." : `Conectar ${meta.label}`}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
