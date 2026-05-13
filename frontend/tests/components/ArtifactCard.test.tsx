import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { ArtifactCard } from '../../src/components/chat/ArtifactCard';
import { useChatStore } from '../../src/store/useChatStore';

describe('ArtifactCard - Componente', () => {
    beforeEach(() => {
        useChatStore.getState().resetState();
    });

    const mockArtifact = {
        artifactId: 'art-123',
        title: 'Analítica de Ventas',
        language: 'csv',
        content: 'v1,v2,v3'
    };

    it('debe renderizar correctamente el título y el lenguaje', () => {
        render(<ArtifactCard {...mockArtifact} />);

        expect(screen.getByText('Analítica de Ventas')).toBeDefined();
        expect(screen.getByText('csv')).toBeDefined();
    });

    it('debe activar el artefacto en el store al hacer clic', () => {
        // IMPORTANTE: El componente busca el artefacto en el store para activarlo
        useChatStore.setState({
            artifacts: [{
                id: 'art-123',
                title: 'Analítica de Ventas',
                type: 'data_table',
                content: 'v1,v2,v3',
                agentId: 'system',
                createdAt: new Date()
            }]
        });

        render(<ArtifactCard {...mockArtifact} />);

        const viewButton = screen.getByText('Ver Código');
        fireEvent.click(viewButton);

        const state = useChatStore.getState();
        expect(state.activeArtifactId).toBe('art-123');
        expect(state.isArtifactPanelOpen).toBe(true);
    });
});
