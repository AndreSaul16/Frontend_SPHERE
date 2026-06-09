import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { DeployStatusResponse } from '@/services/api';

interface DeployState {
    backend: DeployStatusResponse | null;
    backendLoading: boolean;
    backendError: string | null;

    fetchStatus: () => Promise<void>;
}

export const useDeployStore = create<DeployState>()(
    devtools(
        (set) => ({
            backend: null,
            backendLoading: false,
            backendError: null,

            fetchStatus: async () => {
                set({ backendLoading: true, backendError: null });

                try {
                    // Dynamic import to avoid circular dependency in test env
                    const { deployService } = await import('@/services/api');
                    const data = await deployService.getStatus();
                    set({
                        backend: data,
                        backendLoading: false,
                        backendError: null,
                    });
                } catch {
                    set({
                        backend: null,
                        backendLoading: false,
                        backendError: 'Error al consultar estado del backend',
                    });
                }
            },
        }),
        { name: 'DeployStore' }
    )
);
