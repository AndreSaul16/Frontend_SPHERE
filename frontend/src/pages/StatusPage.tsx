import { useEffect } from "react";
import { motion } from "framer-motion";
import { RefreshCw, Server, Globe } from "lucide-react";
import { useDeployStore } from "@/store/useDeployStore";
import { cn } from "@/lib/utils";

function StatusDot({ status }: { status: "live" | "deploying" | "error" | "unknown" }) {
    const colors: Record<string, string> = {
        live: "bg-green-500 shadow-green-500/50",
        deploying: "bg-yellow-500 shadow-yellow-500/50",
        error: "bg-red-500 shadow-red-500/50",
        unknown: "bg-gray-500 shadow-gray-500/30",
    };
    const labels: Record<string, string> = {
        live: "Live",
        deploying: "Deploying",
        error: "Unreachable",
        unknown: "Unknown",
    };

    return (
        <div className="flex items-center gap-2">
            <span
                className={cn(
                    "h-3 w-3 rounded-full shadow-lg",
                    colors[status],
                    status === "deploying" && "animate-pulse"
                )}
            />
            <span className="text-sm font-medium text-text-secondary">{labels[status]}</span>
        </div>
    );
}

function ServiceCard({
    name,
    icon,
    commitSha,
    buildTimestamp,
    version,
    status,
}: {
    name: string;
    icon: React.ReactNode;
    commitSha: string;
    buildTimestamp: string;
    version: string;
    status: "live" | "deploying" | "error" | "unknown";
}) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-panel p-6 rounded-2xl border border-surface-highlight"
        >
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-surface flex items-center justify-center text-electric-cyan">
                        {icon}
                    </div>
                    <h3 className="text-lg font-bold text-text-primary">{name}</h3>
                </div>
                <StatusDot status={status} />
            </div>
            <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                    <span className="text-text-secondary">Commit</span>
                    <span className="text-text-primary font-mono">{commitSha.slice(0, 7)}</span>
                </div>
                {buildTimestamp && (
                    <div className="flex justify-between">
                        <span className="text-text-secondary">Build</span>
                        <span className="text-text-primary">{new Date(buildTimestamp).toLocaleString()}</span>
                    </div>
                )}
                <div className="flex justify-between">
                    <span className="text-text-secondary">Version</span>
                    <span className="text-text-primary">{version}</span>
                </div>
            </div>
        </motion.div>
    );
}

/**
 * Página pública /status — muestra el estado de deploy de todos los servicios.
 * Sin autenticación requerida.
 */
export function StatusPage() {
    const { backend, backendLoading, backendError, fetchStatus } = useDeployStore();

    useEffect(() => {
        fetchStatus();
    }, [fetchStatus]);

    const backendStatus: "live" | "deploying" | "error" | "unknown" = backendError
        ? "error"
        : backend
            ? (backend.deploy_status as "live" | "deploying")
            : backendLoading
                ? "deploying"
                : "unknown";

    // Frontend status from build-time vars
    const frontendSha = (
        typeof __GIT_COMMIT_SHA__ !== "undefined" ? __GIT_COMMIT_SHA__ : "unknown"
    ) as string;
    const frontendTimestamp = (
        typeof __BUILD_TIMESTAMP__ !== "undefined" ? __BUILD_TIMESTAMP__ : ""
    ) as string;
    const frontendVersion = (
        typeof __VERSION__ !== "undefined" ? __VERSION__ : "0.0.0"
    ) as string;

    return (
        <div className="flex-1 h-full flex flex-col items-center justify-center p-6">
            <motion.div
                initial={{ opacity: 0, y: -16 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center mb-8"
            >
                <h1 className="text-3xl font-bold text-text-primary mb-2">
                    Estado del Sistema
                </h1>
                <p className="text-text-secondary">
                    Monitoreo en tiempo real del despliegue
                </p>
            </motion.div>

            <div className="w-full max-w-2xl space-y-4">
                {/* Backend Card */}
                {backendLoading && !backend && !backendError ? (
                    <div className="glass-panel p-6 rounded-2xl border border-surface-highlight flex items-center justify-center">
                        <RefreshCw className="h-5 w-5 text-electric-cyan animate-spin mr-2" />
                        <span className="text-text-secondary">Cargando estado del backend...</span>
                    </div>
                ) : (
                    <ServiceCard
                        name="Backend"
                        icon={<Server className="h-5 w-5" />}
                        commitSha={backend?.commit_sha ?? "unknown"}
                        buildTimestamp={backend?.build_timestamp ?? ""}
                        version={backend?.version ?? "—"}
                        status={backendStatus}
                    />
                )}

                {/* Frontend Card (build-time metadata) */}
                <ServiceCard
                    name="Frontend"
                    icon={<Globe className="h-5 w-5" />}
                    commitSha={frontendSha}
                    buildTimestamp={frontendTimestamp}
                    version={frontendVersion}
                    status="unknown"
                />

                {/* Error + Retry */}
                {backendError && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-center"
                    >
                        <p className="text-red-400 text-sm mb-2">
                            Error al conectar con el backend
                        </p>
                        <button
                            onClick={() => fetchStatus()}
                            className="px-4 py-2 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors text-sm font-medium"
                        >
                            Reintentar
                        </button>
                    </motion.div>
                )}
            </div>
        </div>
    );
}
