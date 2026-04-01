import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useChatStore } from '@/store/useChatStore';
import { chatService } from '@/services/api';

vi.mock('@/services/api', () => ({
    chatService: {
        getCustomAgents: vi.fn(),
        createSession: vi.fn(),
        createCustomAgent: vi.fn(),
    }
}));

describe('Evolved Schema Store Tests', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Reset store manually if needed, or rely on getState() initialization
    });

    it('should correctly map custom agents with nested identity and brain_config', async () => {
        const mockBackendAgents = [
            {
                agent_id: 'agent-123',
                identity: {
                    name: 'Test Agent',
                    role: 'specialist',
                    color: '#ff0000'
                },
                brain_config: {
                    model: 'gpt-4o',
                    temperature: 0.5,
                    system_prompt: 'System prompt content'
                },
                owner_user_id: 'user-1',
                is_public: true
            }
        ];

        (chatService.getCustomAgents as any).mockResolvedValue(mockBackendAgents);

        await useChatStore.getState().fetchCustomAgents();

        const agents = useChatStore.getState().customAgents;
        expect(agents).toHaveLength(1);
        expect(agents[0].id).toBe('agent-123');
        expect(agents[0].name).toBe('Test Agent');
        expect(agents[0].identity?.name).toBe('Test Agent');
        expect(agents[0].brain_config?.model).toBe('gpt-4o');
        expect(agents[0].hexColor).toBe('#ff0000');
    });

    it('should correctly create a new session with visual_config', async () => {
        const mockNewSession = {
            session_id: 'session-456',
            title: 'CEO',
            user_id: 'default_user',
            base_agent_id: 'CEO',
            visual_config: {
                name: 'CEO',
                color: '#ffffff'
            },
            context_files: [],
            enabled_tools: [],
            created_at: new Date().toISOString()
        };

        (chatService.createSession as any).mockResolvedValue(mockNewSession);

        // Mock coreAgents so it finds the CEO
        useChatStore.setState({
            coreAgents: [{ id: 'CEO', role: 'CEO', name: 'CEO', hexColor: '#ffffff' } as any]
        });

        const sessionId = await useChatStore.getState().createNewSession('CEO');

        expect(sessionId).toBe('session-456');
        expect(chatService.createSession).toHaveBeenCalledWith(
            expect.objectContaining({
                title: 'CEO',
                visual_config: expect.objectContaining({ name: 'CEO', color: '#ffffff' }),
                user_id: 'default_user'
            })
        );
    });

    it('should correctly add a custom agent with nested structure', async () => {
        const newAgentInput = {
            identity: { name: 'New Specialist', role: 'specialist', color: '#0000ff' },
            brain_config: { model: 'gpt-4', temperature: 0.8, system_prompt: 'Be helpful' }
        };

        const mockBackendResponse = {
            agent_id: 'new-agent-789',
            ...newAgentInput,
            owner_user_id: 'default_user',
            is_public: false
        };

        (chatService.createCustomAgent as any).mockResolvedValue(mockBackendResponse);

        await useChatStore.getState().addCustomAgent(newAgentInput);

        const agents = useChatStore.getState().customAgents;
        expect(agents).toContainEqual(expect.objectContaining({
            id: 'new-agent-789',
            name: 'New Specialist',
            identity: expect.objectContaining({ name: 'New Specialist' })
        }));
    });
});
