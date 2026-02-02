import { useState, useEffect } from 'react';

const AGENT_AVATAR_STORAGE_KEY = 'sphere_agent_avatars';

/**
 * Hook to get and subscribe to custom agent avatars from localStorage.
 * Returns a map of agentId -> base64 image URL
 */
export function useAgentAvatars() {
    const [avatars, setAvatars] = useState<Record<string, string>>({});

    useEffect(() => {
        const loadAvatars = () => {
            const saved = localStorage.getItem(AGENT_AVATAR_STORAGE_KEY);
            if (saved) {
                try {
                    setAvatars(JSON.parse(saved));
                } catch (e) {
                    console.error('Error parsing avatars:', e);
                }
            }
        };

        // Load initial
        loadAvatars();

        // Listen for storage changes (cross-tab and same-tab custom event)
        const handleStorage = (e: StorageEvent) => {
            if (e.key === AGENT_AVATAR_STORAGE_KEY) {
                loadAvatars();
            }
        };

        const handleAvatarUpdate = () => loadAvatars();

        window.addEventListener('storage', handleStorage);
        window.addEventListener('avatar-updated', handleAvatarUpdate);

        return () => {
            window.removeEventListener('storage', handleStorage);
            window.removeEventListener('avatar-updated', handleAvatarUpdate);
        };
    }, []);

    return avatars;
}

/**
 * Get a single agent's avatar, returns undefined if not set
 */
export function getAgentAvatar(agentId: string): string | undefined {
    const saved = localStorage.getItem(AGENT_AVATAR_STORAGE_KEY);
    if (saved) {
        try {
            const avatars = JSON.parse(saved);
            return avatars[agentId];
        } catch {
            return undefined;
        }
    }
    return undefined;
}

/**
 * Save an agent avatar and dispatch update event
 */
export function saveAgentAvatar(agentId: string, base64Url: string) {
    const saved = localStorage.getItem(AGENT_AVATAR_STORAGE_KEY);
    const avatars = saved ? JSON.parse(saved) : {};
    avatars[agentId] = base64Url;
    localStorage.setItem(AGENT_AVATAR_STORAGE_KEY, JSON.stringify(avatars));

    // Dispatch custom event for same-tab updates
    window.dispatchEvent(new Event('avatar-updated'));
}
