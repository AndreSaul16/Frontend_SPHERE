import { useRef } from "react";
import { ArrowLeft, Save, Camera, Zap, Pencil } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useChatStore, getGroupMembers } from "@/store/useChatStore";
import { cn } from "@/lib/utils";
import { useAgentAvatars, saveAgentAvatar } from "@/hooks/useAgentAvatars";

export function ChatSettingsPage() {
    const navigate = useNavigate();
    const { getAgents, selectedAgentId, updateAgentColor, renameAgent } = useChatStore();
    const agents = getAgents();
    const activeAgent = agents.find(a => a.id === selectedAgentId) || agents[0];
    const avatars = useAgentAvatars();
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Get group members for group chat
    const groupMembers = getGroupMembers(agents);

    const avatarUrl = activeAgent ? avatars[activeAgent.id] : null;

    const handleAvatarChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file && activeAgent) {
            const reader = new FileReader();
            reader.onloadend = () => {
                const base64 = reader.result as string;
                saveAgentAvatar(activeAgent.id, base64);
            };
            reader.readAsDataURL(file);
        }
    };

    const triggerFileInput = () => {
        fileInputRef.current?.click();
    };

    if (!activeAgent) {
        return (
            <div className="flex items-center justify-center h-full text-text-secondary">
                <p>Selecciona un agente primero.</p>
            </div>
        );
    }

    // Extract base name and role for display/edit
    const match = activeAgent.name.match(/^(.+?)\s*\(([A-Z]+)\)$/);
    const baseName = match ? match[1].trim() : activeAgent.name;
    const roleLabel = match ? match[2] : activeAgent.role;
    const isGroupChat = activeAgent.id === 'group-chat';

    const handleNameChange = (newName: string) => {
        if (isGroupChat) {
            renameAgent(activeAgent.id, newName);
        } else {
            // Re-append role for individual agents
            renameAgent(activeAgent.id, `${newName} (${roleLabel})`);
        }
    };

    return (
        <div className="flex flex-col h-full bg-midnight/40 relative overflow-hidden">
            {/* Background Living Effect */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden">
                <div
                    className="aurora-blob w-[60%] h-[60%] top-[-15%] left-[-10%] animate-aurora"
                    style={{ backgroundColor: 'rgba(30, 58, 95, 0.5)' }}
                />
                <div
                    className="aurora-blob w-[45%] h-[45%] bottom-[-10%] right-[-5%] animate-aurora"
                    style={{ backgroundColor: 'rgba(13, 74, 74, 0.4)', animationDelay: '-6s' }}
                />
            </div>

            {/* Header */}
            <div className="h-14 sm:h-16 pl-14 lg:pl-6 pr-3 sm:pr-6 border-b border-surface flex items-center justify-between bg-midnight/90 backdrop-blur-md sticky top-0 z-10">
                <div className="flex items-center gap-3 sm:gap-4">
                    <button
                        onClick={() => navigate(-1)}
                        className="p-2 hover:bg-surface rounded-full transition-colors text-text-secondary hover:text-text-primary"
                    >
                        <ArrowLeft className="h-5 w-5" />
                    </button>
                    <h1 className="text-base sm:text-xl font-bold text-text-primary">Configuración</h1>
                </div>
                <button
                    onClick={() => navigate(-1)}
                    className="flex items-center gap-2 px-3 py-2 bg-electric-cyan/10 text-electric-cyan rounded-xl hover:bg-electric-cyan hover:text-midnight transition-all font-medium text-sm"
                >
                    <Save className="h-4 w-4" />
                    <span className="hidden sm:inline">Guardar</span>
                </button>
            </div>

            {/* Content - Added pb-32 for mobile scrollability */}
            <div className="flex-1 overflow-y-auto p-3 sm:p-8 pb-32 sm:pb-12 scrollbar-thin scrollbar-thumb-surface-highlight">
                <div className="max-w-xl mx-auto space-y-6 sm:space-y-8">

                    {/* Agent Avatar & Identity Section */}
                    <section className="flex flex-col items-center gap-4 sm:gap-6 p-6 sm:p-8 rounded-2xl sm:rounded-3xl bg-surface/60 border border-surface-highlight backdrop-blur-sm text-center">
                        <h2 className="text-text-secondary text-xs sm:text-sm uppercase tracking-widest font-mono">Identidad del Agente</h2>

                        <div className="relative group">
                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleAvatarChange}
                                accept="image/*"
                                className="hidden"
                            />
                            <div
                                onClick={triggerFileInput}
                                className="h-24 w-24 sm:h-32 sm:w-32 rounded-2xl sm:rounded-3xl bg-surface border border-surface-highlight flex items-center justify-center text-3xl sm:text-4xl font-bold shadow-2xl transition-transform group-hover:scale-105 cursor-pointer overflow-hidden"
                            >
                                {avatarUrl ? (
                                    <img src={avatarUrl} alt="Agent Avatar" className="h-full w-full object-cover" />
                                ) : (
                                    <span className={activeAgent.color}>{activeAgent.avatar}</span>
                                )}
                            </div>
                            <button
                                onClick={triggerFileInput}
                                className="absolute -bottom-2 -right-2 p-2 sm:p-2.5 bg-surface border border-surface-highlight rounded-xl text-electric-cyan shadow-lg hover:scale-110 transition-transform"
                            >
                                <Camera className="h-4 w-4 sm:h-5 sm:w-5" />
                            </button>
                        </div>

                        <div className="w-full max-w-sm space-y-4">
                            <div className="space-y-1.5">
                                <label className="text-[10px] text-text-secondary uppercase tracking-widest font-mono block text-left ml-1 opacity-60">
                                    Nombre del Agente
                                </label>
                                <div className="relative group/input">
                                    <input
                                        type="text"
                                        value={isGroupChat ? activeAgent.name : baseName}
                                        onChange={(e) => handleNameChange(e.target.value)}
                                        className="w-full bg-midnight/50 border border-surface-highlight rounded-xl px-4 py-3 text-lg font-bold text-text-primary focus:outline-none focus:border-electric-cyan/50 focus:ring-1 focus:ring-electric-cyan/20 transition-all text-center"
                                        placeholder="Ej: Oberon"
                                    />
                                    <Pencil className="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary/30 group-focus-within/input:text-electric-cyan transition-colors" />
                                </div>
                            </div>

                            <div className="flex flex-col items-center gap-1">
                                <div className="flex items-center gap-2">
                                    {activeAgent.role !== 'system' && (
                                        <span className="px-2 py-0.5 bg-electric-cyan/10 text-electric-cyan rounded text-[10px] font-mono border border-electric-cyan/20">
                                            {roleLabel}
                                        </span>
                                    )}
                                    <h3 className="text-sm font-medium text-text-secondary">Nivel de Cargo</h3>
                                </div>
                                <p className="text-text-secondary/60 text-xs italic">{activeAgent.description}</p>
                            </div>
                        </div>

                        <p className="text-[10px] text-text-secondary/40 max-w-[280px]">
                            La identidad del agente define cómo se presenta en el sistema. Los cambios son instantáneos.
                        </p>
                    </section>

                    {/* Color Settings Section */}
                    <section className="p-6 sm:p-8 rounded-2xl sm:rounded-3xl bg-surface/60 border border-surface-highlight backdrop-blur-sm space-y-4 sm:space-y-6">
                        <div className="flex items-center gap-2">
                            <Zap className="h-4 w-4 text-electric-cyan" />
                            <h2 className="text-text-secondary text-xs sm:text-sm uppercase tracking-widest font-mono">Frecuencia del Experto (Color)</h2>
                        </div>

                        {isGroupChat ? (
                            /* Presets for Group Chat */
                            <div className="grid grid-cols-5 gap-3 sm:gap-4">
                                {[
                                    { name: 'Cyan', hex: '#00F0C8' },
                                    { name: 'Teal', hex: '#00C1B3' },
                                    { name: 'Indigo', hex: '#6B8AFD' },
                                    { name: 'Purple', hex: '#8A63D2' },
                                    { name: 'Magenta', hex: '#E34A95' },
                                ].map((c) => (
                                    <button
                                        key={c.hex}
                                        onClick={() => updateAgentColor(activeAgent.id, c.hex)}
                                        className={cn(
                                            "group relative flex flex-col items-center gap-2 transition-all",
                                            activeAgent.hexColor === c.hex ? "scale-110" : "opacity-60 hover:opacity-100"
                                        )}
                                    >
                                        <div
                                            className={cn(
                                                "h-8 w-8 sm:h-10 sm:w-10 rounded-xl border-2 transition-all duration-300",
                                                activeAgent.hexColor === c.hex ? "shadow-lg" : "border-transparent"
                                            )}
                                            style={{
                                                backgroundColor: `${c.hex}20`,
                                                borderColor: activeAgent.hexColor === c.hex ? c.hex : 'transparent',
                                                boxShadow: activeAgent.hexColor === c.hex ? `0 0 15px ${c.hex}40` : 'none'
                                            }}
                                        >
                                            <div className="h-full w-full flex items-center justify-center">
                                                <div className="h-2 w-2 rounded-full" style={{ backgroundColor: c.hex }} />
                                            </div>
                                        </div>
                                        <span className="text-[8px] sm:text-[10px] font-mono uppercase tracking-tighter opacity-50">{c.name}</span>

                                        {activeAgent.hexColor === c.hex && (
                                            <motion.div
                                                layoutId="activeColor"
                                                className="absolute -inset-1 border border-current rounded-xl opacity-20"
                                                style={{ color: c.hex }}
                                            />
                                        )}
                                    </button>
                                ))}
                            </div>
                        ) : (
                            /* Color Picker for Individual Agents */
                            <div className="flex flex-col items-center gap-6 py-4">
                                <div className="relative group/picker">
                                    <div
                                        className="h-24 w-24 sm:h-28 sm:w-28 rounded-full border-4 shadow-2xl transition-transform duration-500 group-hover/picker:scale-105 flex items-center justify-center relative overflow-hidden"
                                        style={{
                                            borderColor: activeAgent.hexColor,
                                            boxShadow: `0 0 30px ${activeAgent.hexColor}40`,
                                            backgroundColor: `${activeAgent.hexColor}10`
                                        }}
                                    >
                                        <div className="absolute inset-0 bg-gradient-to-tr from-white/10 to-transparent pointer-events-none" />
                                        <input
                                            type="color"
                                            value={activeAgent.hexColor}
                                            onChange={(e) => updateAgentColor(activeAgent.id, e.target.value)}
                                            className="absolute inset-[10%] w-[80%] h-[80%] opacity-0 cursor-pointer z-10"
                                        />
                                        <div className="text-[32px] pointer-events-none z-0" style={{ color: activeAgent.hexColor }}>
                                            🎨
                                        </div>
                                    </div>
                                    <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 px-4 py-1.5 bg-midnight border border-surface-highlight rounded-xl shadow-2xl pointer-events-none flex items-center gap-2 min-w-[100px] justify-center">
                                        <div className="h-2 w-2 rounded-full" style={{ backgroundColor: activeAgent.hexColor }} />
                                        <span className="text-[10px] font-bold font-mono uppercase tracking-widest text-text-primary">
                                            {activeAgent.hexColor}
                                        </span>
                                    </div>
                                </div>
                                <p className="text-[10px] sm:text-xs text-text-secondary/60 italic text-center max-w-[240px] leading-relaxed">
                                    Haz clic en el icono para abrir la rueda de colores y sintonizar la firma espectral del experto.
                                </p>
                            </div>
                        )}

                        <p className="text-[10px] sm:text-xs text-text-secondary/40 leading-relaxed text-center">
                            {isGroupChat
                                ? "Para grupos, el color define el tema visual de la orquestación."
                                : "Afecta al HUD, las burbujas y los efectos visuales de streaming."}
                        </p>
                    </section>

                    {/* Group Members Section - Only for Group Chats */}
                    {isGroupChat && (
                        <section className="p-6 sm:p-8 rounded-2xl sm:rounded-3xl bg-surface/60 border border-surface-highlight backdrop-blur-sm space-y-4 sm:space-y-6">
                            <div className="flex items-center gap-2">
                                <span className="text-lg">👥</span>
                                <h2 className="text-text-secondary text-xs sm:text-sm uppercase tracking-widest font-mono">Miembros del Grupo</h2>
                            </div>

                            <div className="space-y-2">
                                {groupMembers.map((member) => {
                                    const memberAvatar = avatars[member.id];
                                    const memberMatch = member.name.match(/^(.+?)\s*\(([A-Z]+)\)$/);
                                    const memberName = memberMatch ? memberMatch[1].trim() : member.name;
                                    const memberRole = memberMatch ? memberMatch[2] : member.role;

                                    return (
                                        <motion.button
                                            key={member.id}
                                            whileHover={{ scale: 1.02 }}
                                            whileTap={{ scale: 0.98 }}
                                            onClick={() => {
                                                useChatStore.getState().selectAgent(member.id);
                                                navigate('/chat/settings');
                                            }}
                                            className="w-full flex items-center gap-3 p-3 rounded-xl bg-midnight/40 border border-surface-highlight hover:border-electric-cyan/30 transition-all"
                                        >
                                            <div
                                                className="h-10 w-10 rounded-full flex items-center justify-center border overflow-hidden"
                                                style={{ borderColor: `${member.hexColor}40` }}
                                            >
                                                {memberAvatar ? (
                                                    <img src={memberAvatar} alt={member.name} className="h-full w-full object-cover" />
                                                ) : (
                                                    <span className={cn("text-sm font-bold", member.color)}>{member.avatar}</span>
                                                )}
                                            </div>
                                            <div className="flex-1 text-left">
                                                <p className="text-sm font-medium text-text-primary">{memberName}</p>
                                                <p className="text-[10px] text-text-secondary/60 font-mono">{member.description}</p>
                                            </div>
                                            <span
                                                className="px-2 py-1 rounded text-[10px] font-bold font-mono border"
                                                style={{
                                                    color: member.hexColor,
                                                    borderColor: `${member.hexColor}40`,
                                                    backgroundColor: `${member.hexColor}10`
                                                }}
                                            >
                                                {memberRole}
                                            </span>
                                        </motion.button>
                                    );
                                })}
                            </div>

                            <p className="text-[10px] sm:text-xs text-text-secondary/40 leading-relaxed text-center">
                                Haz clic en un miembro para acceder a su configuración individual.
                            </p>
                        </section>
                    )}
                </div>
            </div>
        </div>
    );
}
