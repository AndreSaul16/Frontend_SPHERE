import { Link } from "react-router-dom";
import { Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import { useDeployStore } from "@/store/useDeployStore";

/**
 * Indicador de estado de deploy en el footer del sidebar.
 * Muestra un dot verde (live), amarillo (deploying), rojo (error), o gris (unknown).
 */
export function DeployStatusIndicator() {
    const { backend, backendLoading, backendError } = useDeployStore();

    const status = backendError
        ? "error"
        : backend
            ? backend.deploy_status === "live"
                ? "live"
                : "deploying"
            : backendLoading
                ? "deploying"
                : "unknown";

    const dotColors: Record<string, string> = {
        live: "bg-green-500",
        deploying: "bg-yellow-500 animate-pulse",
        error: "bg-red-500",
        unknown: "bg-gray-500",
    };

    const statusLabels: Record<string, string> = {
        live: "Live",
        deploying: "Deploying",
        error: "Down",
        unknown: "Desconectado",
    };

    return (
        <Link
            to="/status"
            className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-surface/40 border border-transparent hover:border-surface-highlight transition-all text-sm"
        >
            <span
                className={cn(
                    "h-2.5 w-2.5 rounded-full shadow-md",
                    dotColors[status]
                )}
            />
            <span>Deploy</span>
            <span className="text-[11px] text-text-secondary/60 ml-auto">
                {statusLabels[status]}
            </span>
            <Activity className="h-3.5 w-3.5" />
        </Link>
    );
}
