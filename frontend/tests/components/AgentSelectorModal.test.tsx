import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AgentSelectorModal } from '../../src/components/modals/AgentSelectorModal';
import { useChatStore } from '../../src/store/useChatStore';

// Mock de framer-motion
vi.mock('framer-motion', () => ({
    AnimatePresence: ({ children }: any) => children,
    motion: {
        div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
        form: ({ children, ...props }: any) => <form {...props}>{children}</form>,
        button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
    },
}));

describe('AgentSelectorModal - Comportamiento de UI', () => {
    beforeEach(() => {
        useChatStore.getState().resetState();
    });

    it('no debe renderizar nada si el modal está cerrado', () => {
        const { container } = render(
            <MemoryRouter>
                <AgentSelectorModal />
            </MemoryRouter>
        );
        expect(container.firstChild).toBeNull();
    });

    it('debe listar los agentes core y permitir seleccionar uno para iniciar sesión', async () => {
        const createSessionSpy = vi.spyOn(useChatStore.getState(), 'createNewSession').mockResolvedValue('new-s-123');
        useChatStore.setState({ isAgentModalOpen: true });

        render(
            <MemoryRouter>
                <AgentSelectorModal />
            </MemoryRouter>
        );

        // Verificar que agentes core aparecen
        expect(screen.getByText('Nexus (CTO)')).toBeDefined();
        expect(screen.getByText('Oberon (CEO)')).toBeDefined();

        // Seleccionar Nexus
        fireEvent.click(screen.getByText('Nexus (CTO)').closest('button')!);

        expect(createSessionSpy).toHaveBeenCalledWith('cto-1');
    });

    it('debe permitir cambiar a la vista de creación de agente', () => {
        useChatStore.setState({ isAgentModalOpen: true });

        render(
            <MemoryRouter>
                <AgentSelectorModal />
            </MemoryRouter>
        );

        fireEvent.click(screen.getByText('Crear Nuevo Agente'));

        expect(screen.getByText('Crea tu propio experto')).toBeDefined();
        expect(screen.getByPlaceholderText(/Ej: Especialista Legal/i)).toBeDefined();
    });
});
