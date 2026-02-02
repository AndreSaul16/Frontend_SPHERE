export type Role = 'user' | 'system' | 'CTO' | 'CMO' | 'CFO' | 'CEO' | 'specialist';

export interface Agent {
    id: string;
    name: string;
    role: Role;
    avatar: string; // URL o iniciales
    description: string;
    color: string; // Tailwind class (ej: text-agent-cto)
    hexColor: string; // Hex color for HUD animations (ej: #00F0C8)
    isOnline: boolean;
    capabilities?: string[]; // Lista de habilidades del agente
}

export interface Message {
    id: string;
    role: Role;
    content: string; // Markdown
    timestamp: Date;
    agentId?: string; // Si es null, es del sistema o usuario
}

export interface SessionMetadata {
    override_name?: string;
    override_avatar?: string;
    override_color?: string;
    override_role_label?: string;
}

export interface ChatSession {
    session_id: string;
    title: string;
    created_at: string;
    base_agent_id?: string;
    metadata?: SessionMetadata;
}
