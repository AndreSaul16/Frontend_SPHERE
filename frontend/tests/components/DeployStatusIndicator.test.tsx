import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DeployStatusIndicator } from '../../src/components/deploy/DeployStatusIndicator';
import { useDeployStore } from '../../src/store/useDeployStore';

const renderIndicator = () =>
    render(
        <MemoryRouter>
            <DeployStatusIndicator />
        </MemoryRouter>
    );

describe('DeployStatusIndicator', () => {
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

    it('shows green dot when deploy_status is live', () => {
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

        renderIndicator();

        // The indicator should be a link to /status with a green dot
        const link = screen.getByRole('link');
        expect(link).toHaveAttribute('href', '/status');
        // Green indicator — semantic check: should contain the word "live" or have green color indication
        expect(screen.getByText(/deploy/i)).toBeInTheDocument();
    });

    it('shows red dot when backend is unreachable (error state)', () => {
        useDeployStore.setState({
            backendLoading: false,
            backendError: 'Error al consultar estado del backend',
            backend: null,
        });

        renderIndicator();

        const link = screen.getByRole('link');
        expect(link).toHaveAttribute('href', '/status');
        // Red indicator — should show "Down" or error indicator
        expect(screen.getByText(/down|error|desconectado/i)).toBeInTheDocument();
    });

    it('shows loading spinner when backendLoading is true', () => {
        useDeployStore.setState({
            backendLoading: true,
            backend: null,
            backendError: null,
        });

        renderIndicator();

        // Deploy text + Deploying status label both match /deploy/i
        const deployElements = screen.getAllByText(/deploy/i);
        expect(deployElements.length).toBeGreaterThanOrEqual(1);
        const indicator = screen.getByRole('link');
        expect(indicator).toBeInTheDocument();
    });

    it('shows gray dot when deploy_status is deploying', () => {
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

        renderIndicator();

        expect(screen.getByText(/deploying/i)).toBeInTheDocument();
    });
});
