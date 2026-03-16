import { useRef, useState, useEffect } from "react";
import { Send, Square, Paperclip, MoreVertical, Zap, ShieldCheck } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useChatStore, getGroupMembers } from "@/store/useChatStore";
import { MessageBubble } from "./MessageBubble";
import { cn } from "@/lib/utils";

export function ChatPanel() {
    const navigate = useNavigate();
    const { sessionId: urlSessionId } = useParams<{ sessionId: string }>();
    const {
        sessions,
        currentSessionId,
        selectedAgentId,
        getAgents,
        sendMessage,
        stopGeneration,
        streamingSessionIds,
        loadSession,
        getCurrentMessages,
        toggleAgentModal
    } = useChatStore();

    const messages = getCurrentMessages();
    const agents = getAgents();
    const [inputValue, setInputValue] = useState("");
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const isTyping = currentSessionId ? streamingSessionIds.includes(currentSessionId) : false;
    const activeAgent = agents.find(a => a.id === selectedAgentId);
    const currentSession = sessions.find(s => s.session_id === currentSessionId);

    const isGroupChat = selectedAgentId === 'group-chat';
    const groupMembers = getGroupMembers(agents);

    // Color efectivo: priorizar bubble_color de sesión > color de sesión > hexColor del agente
    const effectiveBubbleColor = currentSession?.visual_config?.bubble_color
        || currentSession?.visual_config?.color
        || activeAgent?.hexColor;

    // Priorizar Avatar de la sesión
    const sessionAvatar = currentSession?.visual_config?.avatar;

    const getAgentDisplayInfo = (agent: typeof activeAgent) => {
        if (!agent) return { baseName: 'SPHERE Engine', role: 'CORE' };

        // Overrides desde la sesión
        const overrideName = currentSession?.visual_config?.name;
        const overrideRole = agent.role; // Actualmente no guardamos override_role en visual_config del backend, usamos el del agente

        if (overrideName) {
            return { baseName: overrideName, role: overrideRole };
        }

        const match = agent.name.match(/^(.+?)\s*\(([A-Z]+)\)$/);
        if (match) {
            return { baseName: match[1].trim(), role: match[2] };
        }
        return { baseName: agent.name, role: agent.role };
    };

    const { baseName, role } = getAgentDisplayInfo(activeAgent);

    const getAvatarContent = () => {
        if (sessionAvatar) {
            return <img src={sessionAvatar} alt={activeAgent?.name} className="h-full w-full object-cover" />;
        }
        if (isGroupChat) {
            return <span className="text-xl">🏛️</span>;
        }
        return <span className={cn("font-black text-xl", activeAgent?.color)}>{activeAgent?.avatar || 'S'}</span>;
    };

    const handleSendMessage = () => {
        if (!inputValue.trim()) return;
        sendMessage(inputValue);
        setInputValue("");
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    useEffect(() => {
        if (urlSessionId && urlSessionId !== currentSessionId) {
            loadSession(urlSessionId);
        }
    }, [urlSessionId]);

    const messagesContainerRef = useRef<HTMLDivElement>(null);
    const [isNearBottom, setIsNearBottom] = useState(true);

    const handleScroll = () => {
        const container = messagesContainerRef.current;
        if (!container) return;
        const threshold = 100;
        const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
        setIsNearBottom(distanceFromBottom < threshold);
    };

    useEffect(() => {
        if (isNearBottom) {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages, isTyping, isNearBottom]);

    // ── Welcome Screen: sin sesión activa ──
    if (!currentSessionId && !urlSessionId) {
        return (
            <div className="flex flex-col h-full bg-transparent relative overflow-hidden">
                <div className="flex-1 flex items-center justify-center p-6">
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, ease: "easeOut" }}
                        className="flex flex-col items-center text-center space-y-8 max-w-md"
                    >
                        {/* Logo / Icono central */}
                        <div className="relative">
                            <div className="absolute inset-0 bg-electric-cyan/10 blur-[60px] rounded-full animate-pulse" />
                            <div className="absolute inset-0 bg-luxury-purple/10 blur-[80px] rounded-full animate-pulse [animation-delay:1s]" />
                            <motion.div
                                animate={{ rotate: [0, 5, -5, 0] }}
                                transition={{ repeat: Infinity, duration: 6, ease: "easeInOut" }}
                                className="relative h-28 w-28 rounded-[36px] bg-gradient-to-br from-electric-cyan/10 to-luxury-purple/10 border border-white/10 flex items-center justify-center shadow-2xl backdrop-blur-sm"
                            >
                                <span className="text-5xl">⚡</span>
                            </motion.div>
                        </div>

                        {/* Texto principal */}
                        <div className="space-y-3">
                            <h1 className="text-white font-black text-2xl tracking-tight">
                                SPHERE <span className="text-electric-cyan">Intelligence</span>
                            </h1>
                            <p className="text-gray-400 text-sm leading-relaxed max-w-sm">
                                Tu equipo directivo de IA está listo. CEO, CTO, CMO, CFO — todos los expertos
                                trabajando en sincronía para darte respuestas de nivel ejecutivo.
                            </p>
                        </div>

                        {/* Features rápidos */}
                        <div className="grid grid-cols-2 gap-3 w-full">
                            {[
                                { icon: "🏛️", label: "Junta Directiva", desc: "Orquestación multi-agente" },
                                { icon: "🧠", label: "Expertos IA", desc: "C-Suite especializado" },
                                { icon: "📊", label: "Artifacts", desc: "Código y análisis en vivo" },
                                { icon: "🔒", label: "Encriptado", desc: "Canal seguro E2E" },
                            ].map((feat) => (
                                <div
                                    key={feat.label}
                                    className="p-3 rounded-xl bg-white/[0.02] border border-white/5 text-left hover:border-electric-cyan/20 transition-colors"
                                >
                                    <span className="text-lg">{feat.icon}</span>
                                    <p className="text-white text-xs font-semibold mt-1">{feat.label}</p>
                                    <p className="text-gray-500 text-[10px]">{feat.desc}</p>
                                </div>
                            ))}
                        </div>

                        {/* CTA */}
                        <motion.button
                            whileHover={{ scale: 1.03 }}
                            whileTap={{ scale: 0.97 }}
                            onClick={() => toggleAgentModal(true)}
                            className="w-full py-4 rounded-2xl bg-gradient-to-r from-electric-cyan to-luxury-purple text-white font-bold text-sm uppercase tracking-widest shadow-[0_0_40px_rgba(0,240,200,0.15)] hover:shadow-[0_0_60px_rgba(0,240,200,0.25)] transition-all duration-500"
                        >
                            Iniciar Nuevo Chat
                        </motion.button>

                        <p className="text-[10px] text-gray-600 font-mono uppercase tracking-widest">
                            Powered by SPHERE Neuro-Link v2.0
                        </p>
                    </motion.div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-transparent relative overflow-hidden">
            {/* Header */}
            <header className="h-20 pl-16 lg:pl-8 pr-6 border-b border-white/5 flex items-center justify-between bg-midnight/40 backdrop-blur-xl z-20">
                <div className="flex items-center gap-4 min-w-0 flex-1">
                    <div className="relative">
                        <motion.div
                            layoutId="active-agent-avatar"
                            onClick={() => navigate('/chat/settings')}
                            className={cn(
                                "h-11 w-11 rounded-2xl flex items-center justify-center shadow-2xl overflow-hidden border border-white/10 cursor-pointer hover:border-white/30 transition-colors",
                                isGroupChat ? "bg-gradient-to-tr from-luxury-purple via-electric-cyan to-blue-500" : "bg-white/5"
                            )}
                        >
                            {getAvatarContent()}
                        </motion.div>
                        <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="absolute -bottom-1 -right-1 h-4 w-4 rounded-full bg-emerald-500 border-2 border-midnight shadow-[0_0_10px_rgba(16,185,129,0.5)]"
                        />
                    </div>

                    <div className="min-w-0">
                        <div className="flex items-center gap-2">
                            <h3 className="font-bold text-white text-lg tracking-tight truncate">
                                {isGroupChat ? activeAgent?.name : baseName}
                            </h3>
                            <span className="px-2 py-0.5 bg-white/5 text-gray-500 rounded-lg text-[9px] font-black uppercase tracking-widest border border-white/5">
                                {role}
                            </span>
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                            <ShieldCheck className="h-3 w-3 text-emerald-500/50" />
                            <p className="text-[10px] text-gray-500 font-mono uppercase tracking-tighter">
                                {isGroupChat
                                    ? `${groupMembers.length} Expertos Activos`
                                    : "Canal Encriptado de Extremo a Extremo"}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={() => navigate('/chat/settings')}
                        className="p-2.5 rounded-xl hover:bg-white/5 transition-all text-gray-500 hover:text-white active-scale"
                    >
                        <MoreVertical className="h-5 w-5" />
                    </button>
                </div>
            </header>

            {/* Messages Area */}
            <div
                ref={messagesContainerRef}
                onScroll={handleScroll}
                className="flex-1 overflow-y-auto p-6 scrollbar-none"
            >
                <div className="max-w-4xl mx-auto space-y-8">
                    {messages.length === 0 ? (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex flex-col items-center justify-center py-20 text-center space-y-6"
                        >
                            <div className="relative">
                                <div className="absolute inset-0 bg-luxury-purple/20 blur-3xl rounded-full animate-pulse" />
                                <div className="relative h-20 w-20 rounded-[32px] bg-white/[0.03] border border-white/10 flex items-center justify-center shadow-2xl">
                                    <Zap className="h-10 w-10 text-luxury-purple" />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <h2 className="text-white font-bold text-xl uppercase tracking-widest">Iniciando Protocolo</h2>
                                <p className="text-gray-500 text-sm max-w-xs leading-relaxed">
                                    Canal listo para comunicación de alta fidelidad.
                                    Envía un mensaje para despertar el sistema.
                                </p>
                            </div>
                        </motion.div>
                    ) : (
                        <>
                            {messages.map((msg, idx) => {
                                const msgAgent = msg.agentId ? agents.find(a => a.id === msg.agentId) : (msg.role !== 'user' && msg.role !== 'system' ? activeAgent : undefined);
                                return (
                                    <MessageBubble
                                        key={msg.id}
                                        message={msg}
                                        agent={msgAgent}
                                        agentColor={effectiveBubbleColor}
                                        sessionAvatar={sessionAvatar}
                                        isTyping={isTyping}
                                        isLast={idx === messages.length - 1}
                                    />
                                );
                            })}

                            <AnimatePresence>
                                {isTyping && (
                                    <motion.div
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0 }}
                                        className="flex items-center gap-3 text-gray-500 text-[10px] font-mono uppercase tracking-widest ml-14"
                                    >
                                        <div className="flex gap-1">
                                            <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1.5 }} className="h-1 w-1 rounded-full bg-electric-cyan" />
                                            <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1.5, delay: 0.2 }} className="h-1 w-1 rounded-full bg-electric-cyan" />
                                            <motion.span animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1.5, delay: 0.4 }} className="h-1 w-1 rounded-full bg-electric-cyan" />
                                        </div>
                                        <span>Procesando_Respuesta</span>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                            <div ref={messagesEndRef} />
                        </>
                    )}
                </div>
            </div>

            {/* Input Section */}
            <div className="p-6 bg-gradient-to-t from-midnight/80 to-transparent z-10">
                <div className="max-w-4xl mx-auto">
                    <motion.div
                        initial={false}
                        animate={isTyping ? { opacity: 0.5, y: 10 } : { opacity: 1, y: 0 }}
                        className={cn(
                            "glass-panel rounded-[24px] border border-white/10 p-2 flex items-end gap-2 group transition-all duration-500",
                            !isTyping && "focus-within:border-luxury-purple/40 focus-within:shadow-[0_0_30px_rgba(157,133,255,0.15)] shadow-2xl"
                        )}
                    >
                        <button
                            disabled={isTyping}
                            className="p-3.5 text-gray-500 hover:text-white transition-all disabled:opacity-30 active-scale"
                        >
                            <Paperclip className="h-5 w-5" />
                        </button>

                        <textarea
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder={isTyping ? "Sistema ocupado..." : "Transmite tu consulta..."}
                            className="flex-1 bg-transparent border-none focus:ring-0 text-white placeholder:text-gray-600 resize-none py-3.5 max-h-48 text-[15px] leading-relaxed font-medium"
                            rows={1}
                            disabled={isTyping}
                        />

                        {isTyping ? (
                            <button
                                onClick={stopGeneration}
                                className="p-3.5 rounded-xl transition-all duration-300 bg-red-500/80 text-white shadow-[0_0_20px_rgba(239,68,68,0.4)] hover:bg-red-500 hover:scale-105 animate-pulse"
                                title="Detener generación"
                            >
                                <Square className="h-5 w-5" />
                            </button>
                        ) : (
                            <button
                                onClick={handleSendMessage}
                                disabled={!inputValue.trim()}
                                className={cn(
                                    "p-3.5 rounded-xl transition-all duration-300",
                                    inputValue.trim()
                                        ? "bg-luxury-purple text-white shadow-[0_0_20px_rgba(157,133,255,0.4)] hover:scale-105"
                                        : "bg-white/5 text-gray-600 cursor-not-allowed"
                                )}
                            >
                                <Send className="h-5 w-5" />
                            </button>
                        )}
                    </motion.div>

                    <div className="flex justify-between items-center px-4 mt-3">
                        <div className="flex items-center gap-4">
                            <span className="text-[9px] font-mono text-gray-600 uppercase tracking-widest">Latencia: 24ms</span>
                            <span className="text-[9px] font-mono text-gray-600 uppercase tracking-widest">Tokens: 0.8k/min</span>
                        </div>
                        <p className="text-[9px] text-gray-700 font-mono uppercase tracking-tighter">
                            Powered by SPHERE Neuro-Link v2.0
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
