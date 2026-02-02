import { useState, useEffect } from 'react';
import { Search, X, Zap, Crown, Monitor, TrendingUp, Briefcase, Plus, Users, Cpu, Save, Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChatStore } from '@/store/useChatStore';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import type { Role } from '@/types';

const getRoleIcon = (role: Role) => {
    switch (role) {
        case 'CEO': return Crown;
        case 'CTO': return Monitor;
        case 'CMO': return TrendingUp;
        case 'CFO': return Briefcase;
        case 'system': return Users;
        default: return Zap;
    }
};

export function AgentSelectorModal() {
    const navigate = useNavigate();
    const {
        isAgentModalOpen,
        toggleAgentModal,
        createNewSession,
        getAgents,
        fetchCustomAgents,
        addCustomAgent,
        deleteCustomAgent
    } = useChatStore();

    const [searchQuery, setSearchQuery] = useState("");
    const [isCreating, setIsCreating] = useState(false);
    const [newAgent, setNewAgent] = useState({
        name: "",
        description: "",
        system_prompt: "",
        color: "blue"
    });

    const [isLoadingSession, setIsLoadingSession] = useState(false);
    const [isSavingAgent, setIsSavingAgent] = useState(false);

    useEffect(() => {
        if (isAgentModalOpen) {
            fetchCustomAgents();
        }
    }, [isAgentModalOpen]);

    const allAgents = getAgents();
    const filteredAgents = allAgents.filter((a: any) =>
        a.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        a.description?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const handleSelectAgent = async (agentId: string) => {
        if (isLoadingSession) return;
        setIsLoadingSession(true);
        try {
            const sessionId = await createNewSession(agentId);
            toggleAgentModal(false);
            navigate(`/chat/${sessionId}`);
        } finally {
            setIsLoadingSession(false);
        }
    };

    const handleCreateAgent = async (e: React.FormEvent) => {
        e.preventDefault();
        if (isSavingAgent) return;
        setIsSavingAgent(true);
        try {
            await addCustomAgent(newAgent);
            setIsCreating(false);
            setNewAgent({ name: "", description: "", system_prompt: "", color: "blue" });
        } catch (error) {
            console.error("Error creating agent:", error);
        } finally {
            setIsSavingAgent(false);
        }
    };

    return (
        <AnimatePresence>
            {isAgentModalOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 overflow-hidden">
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => toggleAgentModal(false)}
                        className="absolute inset-0 bg-midnight/80 backdrop-blur-xl"
                    />

                    {/* Modal Content */}
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0, y: 20 }}
                        animate={{ scale: 1, opacity: 1, y: 0 }}
                        exit={{ scale: 0.9, opacity: 0, y: 20 }}
                        className="glass-panel w-full max-w-2xl rounded-[32px] overflow-hidden flex flex-col max-h-[90vh] relative z-10 shadow-[0_0_50px_rgba(0,0,0,0.5)]"
                    >
                        {/* Header */}
                        <div className="p-8 border-b border-white/5 flex items-center justify-between bg-white/[0.02]">
                            <div>
                                <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                                    <div className="p-2 bg-electric-cyan/10 rounded-xl">
                                        {isCreating ? <Plus className="h-6 w-6 text-electric-cyan" /> : <Cpu className="h-6 w-6 text-electric-cyan" />}
                                    </div>
                                    {isCreating ? "Crea tu propio experto" : "Selecciona tu experto"}
                                </h2>
                                <p className="text-sm text-gray-400 mt-2">
                                    {isCreating ? "Define el conocimiento y la personalidad de tu nuevo agente." : "Inicia una nueva línea de trabajo con el perfil adecuado."}
                                </p>
                            </div>
                            <button
                                onClick={() => isCreating ? setIsCreating(false) : toggleAgentModal(false)}
                                className="p-2.5 rounded-full hover:bg-white/5 transition-colors text-gray-400 hover:text-white active-scale"
                            >
                                <X className="h-6 w-6" />
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-white/10">
                            <AnimatePresence mode="wait">
                                {isCreating ? (
                                    <motion.form
                                        key="create-form"
                                        initial={{ opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -20 }}
                                        onSubmit={handleCreateAgent}
                                        className="p-8 space-y-6"
                                    >
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-bold text-gray-500 uppercase tracking-widest ml-1">Nombre del Agente</label>
                                            <input
                                                type="text" required
                                                value={newAgent.name}
                                                onChange={e => setNewAgent({ ...newAgent, name: e.target.value })}
                                                placeholder="Ej: Especialista Legal, Copywriter Senior..."
                                                className="w-full glass-input rounded-2xl py-4 px-6 text-base text-white placeholder:text-gray-600"
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-bold text-gray-500 uppercase tracking-widest ml-1">Descripción corta</label>
                                            <input
                                                type="text" required
                                                value={newAgent.description}
                                                onChange={e => setNewAgent({ ...newAgent, description: e.target.value })}
                                                placeholder="¿En qué ayuda este agente?"
                                                className="w-full glass-input rounded-2xl py-4 px-6 text-base text-white placeholder:text-gray-600"
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-bold text-gray-500 uppercase tracking-widest ml-1">System Prompt (Instrucciones)</label>
                                            <textarea
                                                required rows={5}
                                                value={newAgent.system_prompt}
                                                onChange={e => setNewAgent({ ...newAgent, system_prompt: e.target.value })}
                                                placeholder="Escribe aquí las instrucciones detalladas..."
                                                className="w-full glass-input rounded-2xl py-4 px-6 text-base text-white placeholder:text-gray-600 resize-none"
                                            />
                                        </div>
                                        <div className="pt-4 flex gap-4">
                                            <button
                                                type="button"
                                                onClick={() => setIsCreating(false)}
                                                className="flex-1 py-4 px-6 rounded-2xl bg-white/5 text-white font-bold hover:bg-white/10 transition-colors"
                                            >
                                                Cancelar
                                            </button>
                                            <button
                                                type="submit"
                                                disabled={isSavingAgent}
                                                className="flex-1 py-4 px-6 rounded-2xl bg-electric-cyan text-midnight font-bold hover:brightness-110 active-scale transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                                            >
                                                {isSavingAgent ? <div className="h-5 w-5 border-2 border-midnight/30 border-t-midnight rounded-full animate-spin" /> : <Save className="h-5 w-5" />}
                                                {isSavingAgent ? "Guardando..." : "Guardar Agente"}
                                            </button>
                                        </div>
                                    </motion.form>
                                ) : (
                                    <motion.div
                                        key="agent-list"
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: 20 }}
                                        className="p-8 pt-4 space-y-8"
                                    >
                                        {/* Search Area */}
                                        <div className="relative group">
                                            <Search className="absolute left-5 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-500 group-focus-within:text-electric-cyan transition-colors" />
                                            <input
                                                type="text"
                                                placeholder="Buscar agente..."
                                                value={searchQuery}
                                                onChange={(e) => setSearchQuery(e.target.value)}
                                                className="w-full glass-input rounded-2xl py-4 pl-14 pr-6 text-base text-white placeholder:text-gray-600"
                                            />
                                        </div>

                                        {/* Sections */}
                                        <div className="space-y-8">
                                            {/* Core Section */}
                                            <section>
                                                <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                                                    <Crown className="h-3.5 w-3.5" /> Directiva SPHERE
                                                </h3>
                                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                                    {filteredAgents.filter((a: any) => ['system', 'CEO', 'CTO', 'CMO', 'CFO'].includes(a.role)).map((agent: any) => {
                                                        const Icon = getRoleIcon(agent.role);
                                                        return (
                                                            <motion.button
                                                                whileHover={{ y: -4, scale: 1.02 }}
                                                                whileTap={{ scale: 0.98 }}
                                                                key={agent.id}
                                                                onClick={() => handleSelectAgent(agent.id)}
                                                                className="flex items-center gap-4 p-5 rounded-3xl bg-white/[0.03] border border-white/5 hover:border-electric-cyan/40 hover:bg-white/[0.07] transition-all text-left relative overflow-hidden group shadow-lg"
                                                            >
                                                                <div className={cn(
                                                                    "h-14 w-14 rounded-2xl flex items-center justify-center border shadow-inner",
                                                                    agent.id === 'group-chat' ? "bg-gradient-to-br from-electric-cyan/20 to-luxury-purple/20 border-white/10" : "bg-white/[0.05] border-white/5",
                                                                    agent.color
                                                                )}>
                                                                    <Icon className="h-7 w-7" />
                                                                </div>
                                                                <div className="flex-1 min-w-0">
                                                                    <p className="font-bold text-white group-hover:text-electric-cyan transition-colors">{agent.name}</p>
                                                                    <p className="text-xs text-gray-500 mt-1 line-clamp-1">{agent.description}</p>
                                                                </div>
                                                                <div className="absolute top-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                                    <Zap className="h-3 w-3 text-electric-cyan" />
                                                                </div>
                                                            </motion.button>
                                                        );
                                                    })}
                                                </div>
                                            </section>

                                            {/* Custom Section */}
                                            <section>
                                                <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2">
                                                    <Zap className="h-3.5 w-3.5" /> Mis Expertos
                                                </h3>
                                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                                                    {filteredAgents.filter((a: any) => a.role === 'specialist').map((agent: any) => (
                                                        <motion.div
                                                            key={agent.id}
                                                            whileHover={{ y: -4, scale: 1.02 }}
                                                            className="relative group"
                                                        >
                                                            <button
                                                                onClick={() => handleSelectAgent(agent.id)}
                                                                className="w-full flex items-center gap-4 p-5 rounded-3xl bg-white/[0.03] border border-white/5 hover:border-luxury-purple/40 hover:bg-white/[0.07] transition-all text-left shadow-lg"
                                                            >
                                                                <div className="h-14 w-14 rounded-2xl bg-white/[0.05] border border-white/5 flex items-center justify-center font-bold text-luxury-purple shadow-inner">
                                                                    {agent.avatar}
                                                                </div>
                                                                <div className="flex-1 min-w-0">
                                                                    <p className="font-bold text-white group-hover:text-luxury-purple transition-colors truncate">{agent.name}</p>
                                                                    <p className="text-xs text-gray-500 mt-1 line-clamp-1 truncate">{agent.description}</p>
                                                                </div>
                                                            </button>
                                                            <button
                                                                onClick={(e) => { e.stopPropagation(); deleteCustomAgent(agent.id); }}
                                                                className="absolute top-3 right-3 p-2 opacity-0 group-hover:opacity-100 bg-red-500/10 text-red-400 rounded-xl hover:bg-red-500/20 transition-all active-scale"
                                                            >
                                                                <Trash2 className="h-4 w-4" />
                                                            </button>
                                                        </motion.div>
                                                    ))}

                                                    <motion.button
                                                        whileHover={{ scale: 1.02, backgroundColor: "rgba(255,255,255,0.05)" }}
                                                        whileTap={{ scale: 0.98 }}
                                                        onClick={() => setIsCreating(true)}
                                                        className="flex flex-col items-center justify-center gap-3 p-5 rounded-3xl border-2 border-dashed border-white/5 hover:border-electric-cyan/30 transition-all font-medium text-gray-500 hover:text-electric-cyan"
                                                    >
                                                        <div className="p-3 bg-white/5 rounded-2xl group-hover:bg-electric-cyan/10 transition-colors">
                                                            <Plus className="h-6 w-6" />
                                                        </div>
                                                        <span className="text-sm">Crear Nuevo Agente</span>
                                                    </motion.button>
                                                </div>
                                            </section>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
