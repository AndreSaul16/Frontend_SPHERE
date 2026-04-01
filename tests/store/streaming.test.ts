import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useChatStore } from '../../src/store/useChatStore';
import { server } from '../setup';
import { http, HttpResponse } from 'msw';
import { chatService } from '../../src/services/api';

// Mock simple de chatService
vi.mock('../../src/services/api', () => ({
    chatService: {
        createSession: vi.fn(),
        streamChat: vi.fn(),
        sendMessage: vi.fn(),
        getSessions: vi.fn(),
        getSessionHistory: vi.fn(),
        getCustomAgents: vi.fn(),
        createCustomAgent: vi.fn(),
        deleteCustomAgent: vi.fn()
    }
}));

describe('useChatStore - Integración Streaming SSE', () => {
    beforeEach(() => {
        useChatStore.getState().resetState();
        vi.clearAllMocks();
    });

    it('debe orquestar el flujo completo de un artefacto: open -> chunk -> close', async () => {
        // 1. Mock de creación de sesión (en el service mockeado)
        (chatService.createSession as any).mockResolvedValue({
            session_id: 's-123',
            title: 'Test Session'
        });

        await useChatStore.getState().createNewSession();

        // 2. Simular implementación de streamChat
        (chatService.streamChat as any).mockImplementation(async (query: string, sid: string, callbacks: any) => {
            // Simulamos la secuencia de eventos SSE
            callbacks.onToken('Pensando...');
            callbacks.onArtifactOpen({ title: 'Dynamic Art', artifact_type: 'code', language: 'javascript' });
            callbacks.onArtifactChunk('const a = 1;');
            callbacks.onArtifactChunk(' console.log(a);');
            callbacks.onArtifactClose();
            callbacks.onDone();
        });

        // 3. Ejecutar envío de mensaje
        await useChatStore.getState().sendMessage('Genera código');

        const state = useChatStore.getState();
        const artifacts = state.artifacts;

        // 4. Verificaciones
        expect(artifacts.length).toBe(1);
        expect(artifacts[0].title).toBe('Dynamic Art');
        expect(artifacts[0].content).toBe('const a = 1; console.log(a);');
        expect(state.isArtifactPanelOpen).toBe(true);
        expect(state.activeArtifactId).toBe(artifacts[0].id);
    });
});
