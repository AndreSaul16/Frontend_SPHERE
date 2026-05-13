export type Role = 'user' | 'system' | 'CTO' | 'CMO' | 'CFO' | 'CEO' | 'specialist';

export type SessionType = 'group' | 'direct';

export interface VisualConfig {
    name?: string;
    avatar?: string;
    color?: string;       // Legacy or primary
    theme?: string;       // For groups
    bubble_color?: string; // For direct
    secondary_color?: string;
}

export interface ContextFile {
    file_id: string;
    name: string;
    vector_index_id?: string;
    uploaded_at: string;
}

export interface AgentIdentity {
    name: string;
    role: Role;
    color: string;
    avatar_style?: string;
}

export interface BrainConfig {
    model: string;
    temperature: number;
    system_prompt: string;
}

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
    // Evolved fields
    identity?: AgentIdentity;
    brain_config?: BrainConfig;
    owner_user_id?: string;
    is_public?: boolean;
}

export interface Message {
    id: string;
    role: Role;
    content: string; // Markdown
    timestamp: Date;
    agentId?: string; // Si es null, es del sistema o usuario
}

export interface ChatSession {
    session_id: string;
    user_id: string;
    title: string;
    base_agent_id: string;
    agent_ref_type: string;
    type: SessionType;
    visual_config: VisualConfig;
    context_files: ContextFile[];
    enabled_tools: string[];
    members: string[];
    folder?: string;
    tags?: string[];
    pinned_messages?: string[];
    created_at: string;
}

// --- Agent Templates ---
export interface AgentTemplate {
    template_id: string;
    name: string;
    category: string;
    description: string;
    icon: string;
    system_prompt: string;
    suggested_files: string[];
    default_temperature: number;
    default_model: string;
    tags: string[];
}

// --- Agent Documents ---
export interface AgentDocument {
    file_id: string;
    filename: string;
    file_size_bytes: number;
    content_type: string;
    processing_status: 'pending' | 'processing' | 'completed' | 'failed';
    chunks_count: number;
    uploaded_at: string;
}

// --- Message Rating ---
export interface MessageRating {
    message_id: string;
    rating: 'up' | 'down';
    feedback?: string;
}
