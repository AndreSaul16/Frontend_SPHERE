import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { StatusPage } from '../../src/pages/StatusPage';
import { useDeployStore } from '../../src/store/useDeployStore';

// Mock framer-motion to avoid animation-related test issues
vi.mock('framer-motion', () => {
    const Component = ({ children, ...props }: any) => {
        const { initial, animate, exit, transition, variants, whileHover, ...domProps } = props;
        return <div {...domProps}>{children}</div>;
    };
    return {
        AnimatePresence: ({ children }: any) => children,
        motion: { div: Component },
    };
});

const renderPage = () =>
    render(
        <MemoryRouter>
            <StatusPage />
        </MemoryRouter>
    );

describe('StatusPage', () => {
    beforeEach(() => {
        useDeployStore.setState({
            backend: null,
            backendLoading: false,
            backendError: null,
            fetchStatus: vi.fn().mockResolvedValue(undefined),
        });
        vi.clearAllMocks();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('shows loading skeleton when backendLoading is true', () => {
        useDeployStore.setState({ backendLoading: true, backend: null });

        renderPage();

        // Should show a loading indicator or skeleton
        expect(screen.getByText(/cargando/i)).toBeInTheDocument();
    });

    it('shows backend card with green indicator when deploy_status is live', () => {
        useDeployStore.setState({
            backendLoading: false,
            backendError: null,
            backend: {
                commit_sha: 'abc123def',
                build_timestamp: '2026-06-09T12:00:00Z',
                deploy_status: 'live',
                service_name: 'backend',
                version: 'SPHERE Backend',
            },
        });

        renderPage();

        expect(screen.getByText('Backend')).toBeInTheDocument();
        expect(screen.getByText(/live/i)).toBeInTheDocument();
        expect(screen.getByText('abc123d')).toBeInTheDocument();
    });

    it('shows backend card with yellow indicator when deploy_status is deploying', () => {
        useDeployStore.setState({
            backendLoading: false,
            backendError: null,
            backend: {
                commit_sha: 'unknown',
                build_timestamp: '',
                deploy_status: 'deploying',
                service_name: 'backend',
                version: 'SPHERE Backend',
            },
        });

        renderPage();

        expect(screen.getByText('Backend')).toBeInTheDocument();
        expect(screen.getByText(/deploying/i)).toBeInTheDocument();
        // 'unknown' appears in both backend commit and frontend card — verify at least one
        const unknownElements = screen.getAllByText('unknown');
        expect(unknownElements.length).toBeGreaterThanOrEqual(1);
    });

    it('shows error state with retry button when backendError is set', async () => {
        const mockFetchStatus = vi.fn().mockResolvedValue(undefined);
        useDeployStore.setState({
            backendLoading: false,
            backendError: 'Error al consultar estado del backend',
            backend: null,
            fetchStatus: mockFetchStatus,
        });

        renderPage();

        // useEffect calls fetchStatus on mount → reset the count
        mockFetchStatus.mockClear();

        expect(screen.getByText(/error/i)).toBeInTheDocument();
        const retryButton = screen.getByRole('button', { name: /reintentar/i });
        expect(retryButton).toBeInTheDocument();

        await userEvent.click(retryButton);
        expect(mockFetchStatus).toHaveBeenCalledOnce();
    });

    it('shows frontend card with build-time metadata independent of backend', () => {
        useDeployStore.setState({
            backendLoading: false,
            backendError: 'Error al consultar estado del backend',
            backend: null,
        });

        renderPage();

        // Frontend card should still appear with build-time info
        expect(screen.getByText(/frontend/i)).toBeInTheDocument();
    });
});
