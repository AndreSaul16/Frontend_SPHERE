import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useDeployStore } from '../../src/store/useDeployStore';

describe('useDeployStore', () => {
    beforeEach(() => {
        useDeployStore.setState({
            backend: null,
            backendLoading: false,
            backendError: null,
        });
        global.fetch = vi.fn();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('should initialize with null backend state', () => {
        const state = useDeployStore.getState();
        expect(state.backend).toBeNull();
        expect(state.backendLoading).toBe(false);
        expect(state.backendError).toBeNull();
    });

    it('sets backendLoading=true when fetchStatus starts', async () => {
        (global.fetch as any).mockImplementation(() => new Promise(() => {}));

        const promise = useDeployStore.getState().fetchStatus();
        expect(useDeployStore.getState().backendLoading).toBe(true);

        promise.catch(() => {});
    });

    it('stores backend data on successful fetch', async () => {
        const mockData = {
            commit_sha: 'abc123def',
            build_timestamp: '2026-06-09T12:00:00Z',
            deploy_status: 'live',
            service_name: 'backend',
            version: 'SPHERE Backend',
        };
        (global.fetch as any).mockResolvedValue({
            ok: true,
            json: () => Promise.resolve(mockData),
        });

        await useDeployStore.getState().fetchStatus();

        const state = useDeployStore.getState();
        expect(state.backendLoading).toBe(false);
        expect(state.backendError).toBeNull();
        expect(state.backend).toEqual(mockData);
        expect(state.backend!.deploy_status).toBe('live');
    });

    it('sets error state on fetch failure', async () => {
        (global.fetch as any).mockRejectedValue(new Error('Network error'));

        await useDeployStore.getState().fetchStatus();

        const state = useDeployStore.getState();
        expect(state.backendLoading).toBe(false);
        expect(state.backendError).toBe('Error al consultar estado del backend');
        expect(state.backend).toBeNull();
    });

    it('sets error state on non-OK HTTP response', async () => {
        (global.fetch as any).mockResolvedValue({
            ok: false,
            status: 500,
            json: () => Promise.resolve({ detail: 'Internal error' }),
        });

        await useDeployStore.getState().fetchStatus();

        const state = useDeployStore.getState();
        expect(state.backendLoading).toBe(false);
        expect(state.backendError).toBe('Error al consultar estado del backend');
        expect(state.backend).toBeNull();
    });

    it('clears previous error on successful retry', async () => {
        useDeployStore.setState({ backendError: 'old error' });

        (global.fetch as any).mockResolvedValue({
            ok: true,
            json: () => Promise.resolve({
                commit_sha: 'newsha',
                build_timestamp: '2026-06-09T12:00:00Z',
                deploy_status: 'live',
                service_name: 'backend',
                version: 'SPHERE Backend',
            }),
        });

        await useDeployStore.getState().fetchStatus();

        expect(useDeployStore.getState().backendError).toBeNull();
        expect(useDeployStore.getState().backend!.commit_sha).toBe('newsha');
    });
});
