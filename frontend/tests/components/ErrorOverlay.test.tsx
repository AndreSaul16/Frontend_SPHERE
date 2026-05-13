import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ErrorOverlay } from '../../src/components/common/ErrorOverlay';
import { useChatStore } from '../../src/store/useChatStore';

vi.mock('framer-motion', () => ({
    AnimatePresence: ({ children }: any) => children,
    motion: {
        div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    },
}));

describe('ErrorOverlay - Comportamiento de UI', () => {
    beforeEach(() => {
        useChatStore.getState().resetState();
    });

    it('no debe renderizar nada si no hay errores', () => {
        const { container } = render(<ErrorOverlay />);
        expect(container.firstChild).toBeNull();
    });

    it('debe mostrar el mensaje de error cuando aparece en el store', () => {
        useChatStore.setState({
            errorStates: {
                fetch_agents: null,
                create_session: null,
                send_message: 'Fallo crítico de conexión',
                load_history: null,
                artifact_parser: null,
                core_engine: null
            }
        });

        render(<ErrorOverlay />);

        expect(screen.getByText(/Error del Sistema/i)).toBeDefined();
        expect(screen.getByText('Fallo crítico de conexión')).toBeDefined();
    });
});
