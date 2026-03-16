import { useEffect, useState } from "react";
import { Search, Plus, MoreVertical, Trash2, Share2 } from "lucide-react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useChatStore } from "@/store/useChatStore";
import { useUserAvatar } from "@/hooks/useUserAvatar";

export function Sidebar() {
    const {
        sessions,
        currentSessionId,
        streamingSessionIds,
        toggleSidebar,
        fetchSessions,
        toggleAgentModal,
        coreAgents,
        customAgents
    } = useChatStore();
    const allAgents = [...coreAgents, ...customAgents];
    const userAvatar = useUserAvatar();

    const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
    const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

    // Close menu when clicking outside
    useEffect(() => {
        const handleClickOutside = () => {
            setActiveMenuId(null);
            setConfirmDeleteId(null);
        };
        window.addEventListener('click', handleClickOutside);
        return () => window.removeEventListener('click', handleClickOutside);
    }, []);

    const handleNavClick = () => {
        if (window.innerWidth < 1024) toggleSidebar(false);
    };

    const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
        e.preventDefault();
        e.stopPropagation();
        try {
            await useChatStore.getState().deleteSession(sessionId);
            setActiveMenuId(null);
            setConfirmDeleteId(null);
        } catch (error) {
            console.error("Failed to delete session:", error);
        }
    };

    const toggleMenu = (e: React.MouseEvent, sessionId: string) => {
        e.preventDefault();
        e.stopPropagation();
        setActiveMenuId(activeMenuId === sessionId ? null : sessionId);
        setConfirmDeleteId(null);
    };

    const triggerConfirmDelete = (e: React.MouseEvent, sessionId: string) => {
        e.preventDefault();
        e.stopPropagation();
        setConfirmDeleteId(sessionId);
    };

    // Cargar sesiones al montar
    useEffect(() => {
        fetchSessions();
    }, []);


    return (
        <div className="flex flex-col h-full bg-transparent">
            {/* Header / Search */}
            <div className="p-3 sm:p-4 border-b border-surface-highlight backdrop-blur-md sticky top-0 bg-midnight/80 z-10">
                <h2 className="text-lg sm:text-xl font-bold text-text-primary mb-3 sm:mb-4 tracking-tight">SPHERE</h2>
                <div className="relative group">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary group-focus-within:text-electric-cyan transition-colors" />
                    <input
                        type="text"
                        placeholder="Buscar..."
                        className="w-full bg-surface border border-surface-highlight rounded-xl py-2 pl-9 pr-4 text-sm text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-electric-cyan/50 focus:ring-1 focus:ring-electric-cyan/50 transition-all shadow-inner"
                    />
                </div>
            </div>

            {/* Content Scrollable */}
            <div className="flex-1 overflow-y-auto py-2 space-y-4 scrollbar-thin scrollbar-thumb-surface-highlight scrollbar-track-transparent">

                {/* Action: New Chat Button */}
                <div className="px-3 sm:px-4 pt-2">
                    <button
                        onClick={() => toggleAgentModal(true)}
                        className="w-full py-4 rounded-2xl bg-electric-cyan/10 border border-electric-cyan/30 hover:bg-electric-cyan/20 transition-all duration-300 group flex flex-col items-center justify-center gap-2 shadow-lg shadow-electric-cyan/5"
                    >
                        <div className="h-10 w-10 rounded-full bg-electric-cyan flex items-center justify-center shadow-lg shadow-electric-cyan/20 group-hover:scale-110 transition-transform">
                            <Plus className="h-6 w-6 text-midnight" />
                        </div>
                        <span className="text-sm font-bold text-electric-cyan uppercase tracking-widest">Nuevo Chat</span>
                    </button>
                </div>

                {/* Section: Historial (Sessions) */}
                {sessions.length > 0 && (
                    <div>
                        <h3 className="px-4 text-[10px] font-bold text-text-secondary/40 uppercase tracking-widest mb-2">
                            Historial
                        </h3>
                        <div className="space-y-0.5 sm:space-y-1">
                            {sessions.map((session) => (
                                <div key={session.session_id} className="relative group/item">
                                    <Link
                                        to={`/chat/${session.session_id}`}
                                        onClick={handleNavClick}
                                        className={cn(
                                            "w-full px-3 sm:px-4 py-2.5 flex items-center gap-3 hover:bg-surface-highlight/40 transition-all duration-200 group border-l-2",
                                            currentSessionId === session.session_id
                                                ? "bg-surface-highlight/60 border-electric-cyan shadow-[inset_4px_0_12px_rgba(0,240,200,0.05)]"
                                                : "border-transparent"
                                        )}
                                    >
                                        <div className="h-8 w-8 rounded-full bg-surface border border-surface-highlight flex items-center justify-center flex-shrink-0 text-text-secondary group-hover:text-electric-cyan transition-colors overflow-hidden">
                                            {(() => {
                                                const avatarUrl = session.visual_config?.avatar;
                                                if (avatarUrl) return <img src={avatarUrl} alt="" className="h-full w-full object-cover" />;
                                                const baseAgent = allAgents.find(a => a.id === session.base_agent_id);
                                                if (baseAgent?.avatar) return <span className="text-sm">{baseAgent.avatar}</span>;
                                                return <span className="text-[10px]">💬</span>;
                                            })()}
                                        </div>
                                        <div className="text-left flex-1 min-w-0">
                                            <p className={cn(
                                                "text-sm font-medium truncate flex items-center gap-2",
                                                currentSessionId === session.session_id ? "text-text-primary" : "text-text-secondary group-hover:text-text-primary"
                                            )}>
                                                {session.title}
                                                {streamingSessionIds.includes(session.session_id) && (
                                                    <span className="flex gap-0.5">
                                                        <span className="h-1 w-1 rounded-full bg-electric-cyan animate-bounce [animation-delay:-0.3s]"></span>
                                                        <span className="h-1 w-1 rounded-full bg-electric-cyan animate-bounce [animation-delay:-0.15s]"></span>
                                                        <span className="h-1 w-1 rounded-full bg-electric-cyan animate-bounce"></span>
                                                    </span>
                                                )}
                                            </p>
                                            <p className="text-[10px] text-text-secondary/50 truncate">
                                                {new Date(session.created_at).toLocaleDateString()}
                                            </p>
                                        </div>

                                        {/* Three dots menu button */}
                                        <button
                                            onClick={(e) => toggleMenu(e, session.session_id)}
                                            className={cn(
                                                "p-1 rounded-lg hover:bg-surface-highlight text-text-secondary/0 group-hover/item:text-text-secondary hover:text-text-primary transition-all",
                                                activeMenuId === session.session_id && "text-text-secondary bg-surface-highlight"
                                            )}
                                        >
                                            <MoreVertical className="h-4 w-4" />
                                        </button>
                                    </Link>

                                    {/* Dropdown Menu */}
                                    <AnimatePresence>
                                        {activeMenuId === session.session_id && (
                                            <motion.div
                                                initial={{ opacity: 0, scale: 0.95, y: -10 }}
                                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                                exit={{ opacity: 0, scale: 0.95, y: -10 }}
                                                className="absolute right-2 top-12 z-50 w-36 bg-surface border border-surface-highlight rounded-xl shadow-2xl p-1 backdrop-blur-md"
                                                onClick={(e) => e.stopPropagation()}
                                            >
                                                {confirmDeleteId === session.session_id ? (
                                                    <div className="p-2 space-y-2">
                                                        <p className="text-[10px] text-rose-400 font-bold uppercase tracking-tighter text-center">¿Confirmar borrado?</p>
                                                        <div className="flex gap-1">
                                                            <button
                                                                onClick={(e) => handleDelete(e, session.session_id)}
                                                                className="flex-1 bg-rose-500/20 hover:bg-rose-500/30 text-rose-500 py-1 rounded-lg text-[10px] font-bold transition-colors"
                                                            >
                                                                Sí
                                                            </button>
                                                            <button
                                                                onClick={(e) => { e.preventDefault(); setConfirmDeleteId(null); }}
                                                                className="flex-1 bg-surface-highlight hover:bg-surface-highlight/80 text-text-secondary py-1 rounded-lg text-[10px] font-bold transition-colors"
                                                            >
                                                                No
                                                            </button>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <>
                                                        <button
                                                            onClick={(e) => { e.preventDefault(); /* Placeholder para compartir */ }}
                                                            className="w-full flex items-center gap-2 px-3 py-2 text-xs text-text-secondary hover:text-text-primary hover:bg-surface-highlight rounded-lg transition-colors"
                                                        >
                                                            <Share2 className="h-3.5 w-3.5" />
                                                            Compartir
                                                        </button>
                                                        <div className="h-px bg-surface-highlight my-1 mx-1" />
                                                        <button
                                                            onClick={(e) => triggerConfirmDelete(e, session.session_id)}
                                                            className="w-full flex items-center gap-2 px-3 py-2 text-xs text-rose-400 hover:text-rose-500 hover:bg-rose-500/10 rounded-lg transition-colors"
                                                        >
                                                            <Trash2 className="h-3.5 w-3.5" />
                                                            Eliminar
                                                        </button>
                                                    </>
                                                )}
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* Footer / User Profile */}
            <div className="p-3 sm:p-4 border-t border-surface-highlight bg-midnight/30">
                <Link
                    to="/profile"
                    onClick={() => toggleSidebar(false)}
                    className="flex items-center gap-2.5 sm:gap-3 p-2 rounded-xl border border-transparent hover:border-surface-highlight hover:bg-surface/40 transition-all duration-300 group shadow-lg hover:shadow-electric-cyan/5"
                >
                    <div className="h-8 w-8 sm:h-9 sm:w-9 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm shadow-lg group-hover:scale-105 transition-transform overflow-hidden">
                        {userAvatar ? (
                            <img src={userAvatar} alt="Avatar" className="h-full w-full object-cover" />
                        ) : (
                            "S"
                        )}
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-text-primary group-hover:text-electric-cyan transition-colors truncate">Saúl</p>
                        <p className="text-[11px] sm:text-xs text-text-secondary">Admin</p>
                    </div>
                </Link>
            </div>
        </div>
    );
}

