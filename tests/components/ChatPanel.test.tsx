import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { ChatPanel } from '../../src/components/chat/ChatPanel';
import { useChatStore } from '../../src/store/useChatStore';
import { chatService } from '../../src/services/api';

vi.mock('../../src/services/api', () => ({
    chatService: {
        loadSession: vi.fn(),
        streamChat: vi.fn().mockImplementation(() => new Promise(() => { })),
        getSessions: vi.fn().mockResolvedValue([]),
        getSessionHistory: vi.fn().mockResolvedValue({ messages: [] }),
    }
}));

// Mock de framer-motion simplificado para tests
vi.mock('framer-motion', () => {
    const Component = ({ children, ...props }: any) => {
        const {
            initial, animate, exit, transition,
            layoutId, layout, variants,
            whileHover, whileTap, whileFocus,
            ...domProps
        } = props;
        return <div {...domProps}>{children}</div>;
    };
    return {
        AnimatePresence: ({ children }: any) => children,
        motion: {
            div: Component,
            span: Component,
            h3: Component,
            p: Component,
            header: Component,
            nav: Component,
            button: Component,
            textarea: Component,
        },
        layoutId: 'test-layout-id'
    };
});

describe('ChatPanel - Comportamiento de UI', () => {
    beforeEach(() => {
        useChatStore.getState().resetState();
        vi.clearAllMocks();
    });

    const renderChatPanel = (id = 'test-session') => {
        return render(
            <MemoryRouter initialEntries={[`/chat/${id}`]}>
                <Routes>
                    <Route path="/chat/:sessionId" element={<ChatPanel />} />
                </Routes>
            </MemoryRouter>
        );
    };

    it('debe mostrar el mensaje del usuario inmediatamente al enviar (UI Optimista)', async () => {
        useChatStore.setState({ currentSessionId: 'test-session' });
        renderChatPanel('test-session');

        const input = screen.getByPlaceholderText(/Transmite tu consulta/i);

        fireEvent.change(input, { target: { value: 'Hola SPHERE' } });
        fireEvent.keyDown(input, { key: 'Enter', code: 'Enter', charCode: 13 });

        await waitFor(() => {
            const state = useChatStore.getState();
            const messages = state.messagesBySession['test-session'] || [];
            expect(messages.some(m => m.content === 'Hola SPHERE')).toBe(true);
        });

        expect((input as HTMLTextAreaElement).value).toBe('');
    });

    it('debe bloquear el input mientras hay una respuesta en curso (Streaming)', async () => {
        useChatStore.setState({
            streamingSessionIds: ['test-session'],
            currentSessionId: 'test-session'
        });

        renderChatPanel('test-session');

        const input = await screen.findByPlaceholderText(/Sistema ocupado/i);
        expect(input).toBeDisabled();
    });

    it('debe activar scrollIntoView cuando llegan nuevos mensajes', async () => {
        const scrollSpy = vi.spyOn(window.HTMLElement.prototype, 'scrollIntoView');

        useChatStore.setState({ currentSessionId: 'scroll-test' });
        renderChatPanel('scroll-test');

        useChatStore.setState({
            messagesBySession: {
                'scroll-test': [{ id: '1', role: 'user', content: 'Prueba scroll', timestamp: new Date() }]
            }
        });

        await waitFor(() => {
            expect(scrollSpy).toHaveBeenCalled();
        });
    });
});
