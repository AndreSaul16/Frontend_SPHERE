const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

if (!import.meta.env.VITE_API_URL) {
    console.warn("VITE_API_URL is undefined, using fallback: http://localhost:8000/api/v1");
}

export interface ChatResponse {
    role: string;
    response: string;
}

export interface StreamCallbacks {
    onToken: (content: string) => void;
    onRole: (role: string) => void;
    // ARTIFACTS 2.0 STREAMING: 3-event protocol for live artifact rendering
    onArtifactOpen?: (data: { title: string; artifact_type: string; language: string }) => void;
    onArtifactChunk?: (content: string) => void;
    onArtifactClose?: () => void;
    onDone?: () => void;
    onError?: (error: any) => void;
}

export const chatService = {
    /**
     * Envía un mensaje al orquestador SPHERE (Síncrono/Legacy).
     * @param message El texto del usuario.
     * @param targetRole (Opcional) Rol específico del agente (CTO, CFO, etc.) o undefined para modo orquestado.
     */
    async sendMessage(message: string, targetRole?: string): Promise<ChatResponse> {
        try {
            const response = await fetch(`${API_URL}/chat/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: message,
                    target_role: targetRole,
                }),
            });

            if (!response.ok) {
                throw new Error(`Error del servidor: ${response.status}`);
            }

            const data = await response.json();
            return data as ChatResponse;
        } catch (error) {
            console.error('Error en chatService (sendMessage):', error);
            throw error;
        }
    },

    /**
     * Inicia un flujo SSE para recibir tokens en tiempo real.
     * @param signal - AbortSignal opcional para cancelar la petición si el usuario navega a otro chat.
     */
    async streamChat(
        query: string,
        sessionId: string,
        callbacks: StreamCallbacks,
        targetRole?: string,
        signal?: AbortSignal
    ) {
        try {
            const response = await fetch(`${API_URL}/stream/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query, session_id: sessionId, target_role: targetRole }),
                signal, // Permite cancelar la petición desde fuera
            });

            if (!response.ok) throw new Error(response.statusText);
            if (!response.body) throw new Error("No response body");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                // Check if aborted before reading
                if (signal?.aborted) {
                    reader.cancel();
                    return;
                }

                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;

                // Improved SSE parsing: handle multi-line and partial chunks
                const lines = buffer.split('\n\n');
                buffer = lines.pop() || ''; // Keep incomplete chunk in buffer

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed.startsWith('data: ')) continue;

                    const dataStr = trimmed.replace('data: ', '').trim();

                    if (dataStr === '[DONE]') {
                        callbacks.onDone?.();
                        return;
                    }

                    // Robust JSON parsing with validation
                    try {
                        const data = JSON.parse(dataStr);

                        // Validate expected structure before processing
                        if (typeof data !== 'object' || data === null) {
                            console.warn("SSE: Received non-object data, skipping");
                            continue;
                        }

                        if (data.type === 'token' && typeof data.content === 'string') {
                            callbacks.onToken(data.content);
                        } else if (data.type === 'meta' && data.role) {
                            callbacks.onRole(data.role);
                        } else if (data.type === 'artifact_open') {
                            callbacks.onArtifactOpen?.({
                                title: data.title || 'untitled',
                                artifact_type: data.artifact_type || 'code',
                                language: data.language || ''
                            });
                        } else if (data.type === 'artifact_chunk' && typeof data.content === 'string') {
                            callbacks.onArtifactChunk?.(data.content);
                        } else if (data.type === 'artifact_close') {
                            callbacks.onArtifactClose?.();
                        } else if (data.type === 'error') {
                            throw new Error(data.message || 'Unknown server error');
                        }
                    } catch (parseError) {
                        // Log but don't crash - continue processing other chunks
                        console.warn("SSE: Error parsing chunk, skipping:", parseError, "Data:", dataStr.substring(0, 100));
                    }
                }
            }

            // Process any remaining buffer content after stream ends
            if (buffer.trim()) {
                console.warn("SSE: Unprocessed buffer content at end:", buffer.substring(0, 100));
            }

        } catch (error) {
            // Don't trigger error callback if request was intentionally aborted
            if (signal?.aborted) {
                console.log("SSE: Request aborted by user navigation");
                return;
            }
            console.error("🔥 Error en streamChat:", error);
            callbacks.onError?.(error);
        }
    },

    /**
     * Gestión de Sesiones
     */
    async createSession(title?: string): Promise<any> {
        const response = await fetch(`${API_URL}/sessions/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title })
        });
        if (!response.ok) {
            throw new Error(`Error creating session: ${response.status} ${response.statusText}`);
        }
        return response.json();
    },

    async getSessions(): Promise<any[]> {
        const response = await fetch(`${API_URL}/sessions/`);
        if (!response.ok) {
            throw new Error(`Error fetching sessions: ${response.status}`);
        }
        return response.json();
    },

    async getSessionHistory(sessionId: string): Promise<any> {
        const response = await fetch(`${API_URL}/sessions/${sessionId}/history`);
        return response.json();
    },

    // --- AGENTS CUSTOM ---
    async getCustomAgents(): Promise<any[]> {
        const response = await fetch(`${API_URL}/agents/`);
        return response.json();
    },

    async createCustomAgent(data: { name: string, description: string, system_prompt: string, color?: string }): Promise<any> {
        const response = await fetch(`${API_URL}/agents/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return response.json();
    },

    async deleteCustomAgent(agentId: string): Promise<void> {
        await fetch(`${API_URL}/agents/${agentId}`, { method: 'DELETE' });
    }
};
