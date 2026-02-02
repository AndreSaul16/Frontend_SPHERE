import { create } from 'zustand';
import type { Agent, Message, Role, ChatSession } from '../types';
import type { Artifact } from '../types/artifact';
import { v4 as uuidv4 } from 'uuid';
import { chatService } from '../services/api';
import { NetworkError, SessionError, type ErrorContext } from '../lib/errors';

interface ChatState {
    coreAgents: Agent[];
    customAgents: Agent[];
    sessions: ChatSession[];
    currentSessionId: string | null;
    selectedAgentId: string | null;
    messagesBySession: Record<string, Message[]>;
    sessionsByAgent: Record<string, string>; // agentId → sessionId (aislamiento de chats)
    streamingSessionIds: string[];
    isAgentModalOpen: boolean;
    isArtifactPanelOpen: boolean;
    isSidebarOpen: boolean;
    artifacts: Artifact[];
    activeArtifactId: string | null;
    errorStates: Record<ErrorContext, string | null>; // Errores por método

    // Acciones
    fetchCustomAgents: () => Promise<void>;
    addCustomAgent: (data: any) => Promise<void>;
    deleteCustomAgent: (id: string) => Promise<void>;
    toggleAgentModal: (open?: boolean) => void;
    getAgents: () => Agent[];
    fetchSessions: () => Promise<void>;
    createNewSession: (agentId?: string) => Promise<string>;
    loadSession: (sessionId: string) => Promise<void>;
    selectAgent: (agentId: string) => void;
    toggleSidebar: (open?: boolean) => void;
    sendMessage: (content: string) => Promise<void>;
    toggleArtifactPanel: () => void;
    renameAgent: (id: string, newName: string) => void;
    updateAgentColor: (id: string, newHexColor: string) => void;
    addArtifact: (artifact: Artifact) => void;
    setActiveArtifact: (id: string | null) => void;
    resetState: () => void;

    // Selector
    getCurrentMessages: () => Message[];
    getArtifacts: () => Artifact[];
}

// Saludos personalizados por agente (sin gastar tokens)
const AGENT_GREETINGS: Record<string, string> = {
    'group-chat': 'Bienvenido a la **Junta Directiva** de SPHERE. El Router analizará tu consulta y delegará al agente más adecuado.',
    'ceo-1': '¡Hola! Soy **Oberon**, tu CEO estratégico. Estoy aquí para ofrecerte visión de alto nivel, decisiones ejecutivas y liderazgo empresarial. ¿En qué puedo ayudarte?',
    'cto-1': '¡Saludos! Soy **Nexus**, tu CTO. Mi expertise incluye arquitectura cloud, DevOps, seguridad técnica y decisiones de infraestructura. ¿Cuál es tu desafío técnico?',
    'cmo-1': '¡Bienvenido! Soy **Vortex**, tu CMO. Me especializo en estrategia de marketing, branding, growth hacking y posicionamiento de mercado. ¿Qué necesitas impulsar?',
    'cfo-1': '¡Hola! Soy **Ledger**, tu CFO. Puedo ayudarte con análisis financiero, gestión de riesgos, proyecciones y optimización de costes. ¿Qué números analizamos?',
};

// Lista de Agentes
const MOCK_AGENTS: Agent[] = [
    {
        id: 'group-chat',
        name: 'Junta Directiva',
        role: 'system',
        avatar: '🏛️',
        description: 'Orquestación completa - El Router decide quién responde.',
        color: 'text-text-secondary',
        hexColor: '#00F0C8', // Cyan Electrico (Default)
        isOnline: true,
        capabilities: ['Análisis Estratégico', 'Decisiones Ejecutivas', 'Coordinación Multi-agente'],
    },
    {
        id: 'ceo-1',
        name: 'Oberon (CEO)',
        role: 'CEO',
        avatar: 'O',
        description: 'Visión estratégica y liderazgo ejecutivo.',
        color: 'text-agent-ceo',
        hexColor: '#8A63D2', // Purple
        isOnline: true,
        capabilities: ['Estrategia Corporativa', 'Toma de Decisiones', 'Visión de Negocio'],
    },
    {
        id: 'cto-1',
        name: 'Nexus (CTO)',
        role: 'CTO',
        avatar: 'N',
        description: 'Experto en Arquitectura Cloud y DevOps.',
        color: 'text-agent-cto',
        hexColor: '#00C1B3', // Teal
        isOnline: true,
        capabilities: ['Cloud Architecture', 'DevOps', 'Seguridad Técnica'],
    },
    {
        id: 'cmo-1',
        name: 'Vortex (CMO)',
        role: 'CMO',
        avatar: 'V',
        description: 'Estratega de Mercado y Posicionamiento.',
        color: 'text-agent-cmo',
        hexColor: '#E34A95', // Magenta
        isOnline: true,
        capabilities: ['Marketing Digital', 'Branding', 'Growth Hacking'],
    },
    {
        id: 'cfo-1',
        name: 'Ledger (CFO)',
        role: 'CFO',
        avatar: 'L',
        description: 'Auditor Financiero y Gestión de Riesgos.',
        color: 'text-agent-cfo',
        hexColor: '#6B8AFD', // Indigo
        isOnline: true,
        capabilities: ['Análisis Financiero', 'Gestión de Riesgos', 'Proyecciones'],
    },
];

// Helper: crear mensaje de saludo
const createGreeting = (agentId: string, agents: Agent[]): Message => {
    const agent = agents.find(a => a.id === agentId);
    return {
        id: uuidv4(),
        role: agentId === 'group-chat' ? 'system' : (agent?.role || 'system'),
        content: AGENT_GREETINGS[agentId] || `Conectado con ${agent?.name || 'agente'}.`,
        timestamp: new Date(),
        agentId: agentId !== 'group-chat' ? agentId : undefined,
    };
};

// Helpers
export const getGroupMembers = (agents: Agent[]) => agents.filter(a => a.id !== 'group-chat');

export const useChatStore = create<ChatState>((set, get) => ({
    coreAgents: MOCK_AGENTS,
    customAgents: [],
    sessions: [],
    currentSessionId: null,
    selectedAgentId: 'group-chat',
    messagesBySession: {},
    sessionsByAgent: {}, // Mapeo agente → sesión para aislamiento de chats
    streamingSessionIds: [],
    isAgentModalOpen: false,
    isArtifactPanelOpen: false,
    isSidebarOpen: true,
    artifacts: [],
    activeArtifactId: null,
    errorStates: {
        fetch_agents: null,
        create_session: null,
        send_message: null,
        load_history: null,
        artifact_parser: null,
        core_engine: null
    },

    // Selectores
    getCurrentMessages: () => {
        const { currentSessionId, messagesBySession } = get();
        return currentSessionId ? (messagesBySession[currentSessionId] || []) : [];
    },

    getArtifacts: () => get().artifacts,

    // Helper para obtener todos los agentes (Core + Custom)
    getAgents: () => [...get().coreAgents, ...get().customAgents],

    fetchSessions: async () => {
        try {
            const sessions = await chatService.getSessions();
            set({ sessions });
        } catch (error) {
            console.error('Error fetching sessions:', error);
        }
    },

    fetchCustomAgents: async () => {
        set((state) => ({ errorStates: { ...state.errorStates, fetch_agents: null } }));
        try {
            const customAgentsData = await chatService.getCustomAgents();
            // Mapear de Response a Agent tipo frontend
            const mapped: Agent[] = customAgentsData.map((a: any) => ({
                id: a.agent_id,
                name: a.name,
                role: a.role as Role,
                description: a.description,
                avatar: a.name.charAt(0).toUpperCase(),
                color: 'bg-surface border-white/5',
                hexColor: a.color || '#00f2ff',
                isOnline: true
            }));
            set({ customAgents: mapped });
        } catch (error: any) {
            const sphereError = new NetworkError('Error al obtener agentes personalizados', 'fetch_agents', error);
            set((state) => ({ errorStates: { ...state.errorStates, fetch_agents: sphereError.message } }));
        }
    },

    addCustomAgent: async (data) => {
        set((state) => ({ errorStates: { ...state.errorStates, fetch_agents: null } }));
        try {
            const newAgentData = await chatService.createCustomAgent(data);
            const mapped: Agent = {
                id: newAgentData.agent_id,
                name: newAgentData.name,
                role: newAgentData.role as Role,
                description: newAgentData.description,
                avatar: newAgentData.name.charAt(0).toUpperCase(),
                color: 'bg-surface border-white/5',
                hexColor: newAgentData.color || '#00f2ff',
                isOnline: true
            };
            set(state => ({ customAgents: [mapped, ...state.customAgents] }));
        } catch (error: any) {
            const sphereError = new NetworkError('Error al crear agente personalizado', 'fetch_agents', error);
            set((state) => ({ errorStates: { ...state.errorStates, fetch_agents: sphereError.message } }));
            throw sphereError; // Re-throw to allow UI to handle specific error
        }
    },

    deleteCustomAgent: async (id) => {
        try {
            await chatService.deleteCustomAgent(id);
            set(state => ({ customAgents: state.customAgents.filter(a => a.id !== id) }));
        } catch (error) {
            console.error('Error deleting custom agent:', error);
        }
    },

    createNewSession: async (agentId) => {
        set((state) => ({ errorStates: { ...state.errorStates, create_session: null } }));
        try {
            const targetId = agentId || 'group-chat';
            const allAgents = [...get().coreAgents, ...get().customAgents];
            const agent = allAgents.find(a => a.id === targetId);
            const title = agent ? `Chat con ${agent.name}` : 'Nueva Sesión';

            const newSession = await chatService.createSession(
                title,
                agent?.role || 'CEO',
                null // Metadata is empty for now until UI is added
            );
            const sessionId = newSession.session_id;

            set((state) => ({
                currentSessionId: sessionId,
                selectedAgentId: targetId,
                messagesBySession: {
                    ...state.messagesBySession,
                    [sessionId]: [createGreeting(targetId, allAgents)]
                },
                sessions: [newSession, ...state.sessions],
                sessionsByAgent: {
                    ...state.sessionsByAgent,
                    [targetId]: sessionId
                },
                errorStates: { ...state.errorStates, create_session: null }
            }));

            return sessionId;
        } catch (error: any) {
            const sphereError = new SessionError('Error al crear la sesión', 'create_session', error);
            set((state) => ({
                errorStates: { ...state.errorStates, create_session: sphereError.message }
            }));
            throw sphereError;
        }
    },

    loadSession: async (sessionId) => {
        const { messagesBySession, coreAgents, customAgents } = get();
        const allAgents = [...coreAgents, ...customAgents];

        set((state) => ({
            errorStates: { ...state.errorStates, load_history: null }
        }));

        if (messagesBySession[sessionId] && messagesBySession[sessionId].length > 0) {
            // Detectar el agentId de la sesión en caché
            const cachedMessages = messagesBySession[sessionId];
            const agentIds = cachedMessages
                .filter(m => m.agentId && m.agentId !== 'system')
                .map(m => m.agentId);
            const detectedAgentId = agentIds.length > 0 ? agentIds[0] : 'group-chat';

            console.log('📦 [loadSession] Cache:', { sessionId, detectedAgentId, agentIds });
            set({ currentSessionId: sessionId, selectedAgentId: detectedAgentId });
            return;
        }

        set((state) => ({
            streamingSessionIds: [...state.streamingSessionIds, sessionId]
        }));

        try {
            const history = await chatService.getSessionHistory(sessionId);
            const sessionArtifacts: Artifact[] = [];
            const mappedMessages: Message[] = history.messages.map((m: any, idx: number) => {
                let role: Role = 'system';
                if (m.type === 'human') role = 'user';
                else if (m.type === 'ai') {
                    const agentId = m.additional_kwargs?.agent_id;
                    const agent = allAgents.find(a => a.id === agentId);
                    // IMPORTANTE: Si es AI, nunca debe ser 'system' para evitar el estilo de "pill" del sistema
                    role = (agent ? agent.role : 'assistant') as Role;
                }

                // --- LÓGICA DE RECUPERACIÓN DE ARTEFACTOS ---
                // El backend guarda los artefactos persistidos como XML dentro del contenido
                let processedContent = m.content;
                const artifactRegex = /<sphere_artifact\s+([^>]+)>([\s\S]*?)<\/sphere_artifact>/g;

                let match;
                while ((match = artifactRegex.exec(m.content)) !== null) {
                    const [fullTag, attrsStr, content] = match;

                    const titleMatch = /title=\\?"([^\\"]+)\\?"/.exec(attrsStr);
                    const typeMatch = /artifact_type=\\?"([^\\"]+)\\?"/.exec(attrsStr);
                    const langMatch = /language=\\?"([^\\"]*)\\?"/.exec(attrsStr);

                    const title = titleMatch ? titleMatch[1] : "untitled";
                    const rawType = typeMatch ? typeMatch[1] : "code";
                    const language = langMatch ? langMatch[1] : "";

                    const typeMap: Record<string, 'code' | 'markdown' | 'mermaid' | 'data_table'> = {
                        'code': 'code', 'markdown': 'markdown', 'mermaid': 'mermaid', 'csv': 'data_table',
                    };

                    const artifactId = uuidv4();
                    const artifact: Artifact = {
                        id: artifactId,
                        title,
                        type: typeMap[rawType] || 'code',
                        language: language || undefined,
                        content: content.trim(),
                        agentId: m.additional_kwargs?.agent_id || 'system',
                        createdAt: new Date(m.additional_kwargs?.timestamp || Date.now()),
                    };

                    sessionArtifacts.push(artifact);
                    // Reemplazamos el XML por nuestro formato interno que MessageBubble entiende
                    processedContent = processedContent.replace(fullTag, `\n\n[ARTIFACT:${artifactId}:${title}]\n\n`);
                }

                return {
                    id: `history-${sessionId}-${idx}`,
                    role,
                    content: processedContent,
                    timestamp: new Date(m.additional_kwargs?.timestamp || Date.now()),
                    agentId: m.additional_kwargs?.agent_id || undefined
                };
            });

            set((state) => {
                // Detectar el agentId predominante en la sesión
                const agentIds = mappedMessages
                    .filter(m => m.agentId && m.agentId !== 'system')
                    .map(m => m.agentId);
                const detectedAgentId = agentIds.length > 0 ? agentIds[0] : 'group-chat';

                console.log('🌐 [loadSession] Servidor:', { sessionId, detectedAgentId, agentIds });

                return {
                    currentSessionId: sessionId,
                    selectedAgentId: detectedAgentId,
                    artifacts: [...state.artifacts, ...sessionArtifacts],
                    messagesBySession: {
                        ...state.messagesBySession,
                        [sessionId]: mappedMessages
                    },
                    streamingSessionIds: state.streamingSessionIds.filter(id => id !== sessionId)
                };
            });
        } catch (error: any) {
            const sphereError = new NetworkError(
                'Fallo al recuperar el historial de la sesión',
                'load_history',
                error
            );
            set((state) => ({
                currentSessionId: sessionId,
                streamingSessionIds: state.streamingSessionIds.filter(id => id !== sessionId),
                errorStates: { ...state.errorStates, load_history: sphereError.message }
            }));
        }
    },

    addArtifact: (artifact) => set((state) => ({
        artifacts: [...state.artifacts, artifact],
        activeArtifactId: artifact.id,
        isArtifactPanelOpen: true,
    })),

    setActiveArtifact: (id) => set({
        activeArtifactId: id,
        isArtifactPanelOpen: true
    }),

    selectAgent: (agentId) => {
        set({ selectedAgentId: agentId });
        console.log(`🔌 Canal seleccionado: ${agentId}`);
    },

    toggleArtifactPanel: () => set((state) => ({ isArtifactPanelOpen: !state.isArtifactPanelOpen })),

    renameAgent: (id, newName) => {
        set((state) => ({
            coreAgents: state.coreAgents.map(agent =>
                agent.id === id ? { ...agent, name: newName } : agent
            ),
            customAgents: state.customAgents.map(agent =>
                agent.id === id ? { ...agent, name: newName } : agent
            ),
        }));
    },

    updateAgentColor: (id, newHexColor) => {
        set((state) => ({
            coreAgents: state.coreAgents.map(agent =>
                agent.id === id ? { ...agent, hexColor: newHexColor } : agent
            ),
            customAgents: state.customAgents.map(agent =>
                agent.id === id ? { ...agent, hexColor: newHexColor } : agent
            ),
        }));
    },

    toggleSidebar: (open) => set((state) => ({
        isSidebarOpen: open !== undefined ? open : !state.isSidebarOpen
    })),

    toggleAgentModal: (open) => set((state) => ({
        isAgentModalOpen: open !== undefined ? open : !state.isAgentModalOpen
    })),

    sendMessage: async (content) => {
        const { currentSessionId, selectedAgentId } = get();
        const allAgents = [...get().coreAgents, ...get().customAgents];

        let sessionId = currentSessionId;
        if (!sessionId) {
            sessionId = await get().createNewSession(selectedAgentId || undefined);
        }

        const userMsg: Message = {
            id: uuidv4(),
            role: 'user',
            content,
            timestamp: new Date(),
        };

        // Añadir al historial de la sesión específica
        set((state) => ({
            messagesBySession: {
                ...state.messagesBySession,
                [sessionId!]: [...(state.messagesBySession[sessionId!] || []), userMsg]
            },
            streamingSessionIds: [...state.streamingSessionIds, sessionId!],
            errorStates: { ...state.errorStates, send_message: null } // Clear previous error
        }));

        try {
            const selectedAgent = allAgents.find(a => a.id === selectedAgentId);
            const targetRole: Role | undefined =
                (selectedAgentId === 'group-chat' || !selectedAgent) ? undefined : selectedAgent?.role;

            const botMsgId = uuidv4();
            const botMsg: Message = {
                id: botMsgId,
                role: (targetRole || 'system') as Role,
                content: '',
                timestamp: new Date(),
                agentId: selectedAgentId || undefined,
            };

            set((state) => ({
                messagesBySession: {
                    ...state.messagesBySession,
                    [sessionId!]: [...(state.messagesBySession[sessionId!] || []), botMsg]
                },
            }));

            // Usar una referencia local al sessionId para los callbacks
            const targetSessionId = sessionId!;

            await chatService.streamChat(
                content,
                targetSessionId,
                {
                    onToken: (token) => {
                        set((state) => ({
                            messagesBySession: {
                                ...state.messagesBySession,
                                [targetSessionId]: (state.messagesBySession[targetSessionId] || []).map(msg =>
                                    msg.id === botMsgId
                                        ? { ...msg, content: msg.content + token }
                                        : msg
                                ),
                            },
                        }));
                    },
                    onRole: (role) => {
                        set((state) => ({
                            messagesBySession: {
                                ...state.messagesBySession,
                                [targetSessionId]: (state.messagesBySession[targetSessionId] || []).map(msg =>
                                    msg.id === botMsgId
                                        ? { ...msg, role: role as Role }
                                        : msg
                                ),
                            },
                        }));
                    },
                    onArtifactOpen: (data) => {
                        const typeMap: Record<string, 'code' | 'markdown' | 'mermaid' | 'data_table'> = {
                            'code': 'code', 'markdown': 'markdown', 'mermaid': 'mermaid', 'csv': 'data_table',
                        };

                        const artifactId = uuidv4();
                        const artifact: Artifact = {
                            id: artifactId,
                            title: data.title,
                            type: typeMap[data.artifact_type] || 'code',
                            language: data.language || undefined,
                            content: '',
                            agentId: selectedAgentId || 'system',
                            createdAt: new Date(),
                        };

                        get().addArtifact(artifact);

                        set((state) => ({
                            messagesBySession: {
                                ...state.messagesBySession,
                                [targetSessionId]: (state.messagesBySession[targetSessionId] || []).map(msg =>
                                    msg.id === botMsgId
                                        ? { ...msg, content: msg.content + `\n\n[ARTIFACT:${artifactId}:${data.title}]\n\n` }
                                        : msg
                                ),
                            },
                        }));

                        // @ts-ignore
                        window[`__streamingArtifact_${targetSessionId}`] = artifactId;
                    },
                    onArtifactChunk: (content) => {
                        // @ts-ignore
                        const artifactId = window[`__streamingArtifact_${targetSessionId}`];
                        if (!artifactId) return;

                        set((state) => ({
                            artifacts: state.artifacts.map(a =>
                                a.id === artifactId ? { ...a, content: a.content + content } : a
                            )
                        }));
                    },
                    onArtifactClose: () => {
                        // @ts-ignore
                        window[`__streamingArtifact_${targetSessionId}`] = null;
                    },
                    onDone: () => {
                        set((state) => ({
                            streamingSessionIds: state.streamingSessionIds.filter(id => id !== targetSessionId),
                        }));
                    },
                    onError: () => {
                        set((state) => ({
                            messagesBySession: {
                                ...state.messagesBySession,
                                [targetSessionId]: (state.messagesBySession[targetSessionId] || []).map(msg =>
                                    msg.id === botMsgId
                                        ? { ...msg, content: msg.content + '\n\n⚠️ **Error de conexión.**' }
                                        : msg
                                ),
                            },
                            streamingSessionIds: state.streamingSessionIds.filter(id => id !== targetSessionId),
                        }));
                    }
                },
                (targetRole as any) === "specialist" ? (selectedAgentId || undefined) : targetRole
            );
        } catch (error: any) {
            const sphereError = new NetworkError('Error en el flujo de transmisión', 'send_message', error);
            set((state) => ({
                streamingSessionIds: state.streamingSessionIds.filter(id => id !== sessionId),
                errorStates: { ...state.errorStates, send_message: sphereError.message }
            }));
            // @ts-ignore
            window[`__streamingArtifact_${sessionId}`] = null;
        }
    },

    resetState: () => set({
        messagesBySession: {},
        artifacts: [],
        currentSessionId: null,
        streamingSessionIds: [],
        errorStates: {
            fetch_agents: null,
            create_session: null,
            send_message: null,
            load_history: null,
            artifact_parser: null,
            core_engine: null
        }
    })
}));
