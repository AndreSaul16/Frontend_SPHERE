import { useState, useEffect } from 'react';

const USER_AVATAR_STORAGE_KEY = 'sphere_user_avatar';

/**
 * Hook to get and subscribe to user avatar from localStorage.
 * Returns the base64 image URL or null if not set.
 */
export function useUserAvatar() {
    const [avatar, setAvatar] = useState<string | null>(null);

    useEffect(() => {
        const loadAvatar = () => {
            const saved = localStorage.getItem(USER_AVATAR_STORAGE_KEY);
            setAvatar(saved);
        };

        // Load initial
        loadAvatar();

        // Listen for storage changes (cross-tab)
        const handleStorage = (e: StorageEvent) => {
            if (e.key === USER_AVATAR_STORAGE_KEY) {
                loadAvatar();
            }
        };

        // Listen for same-tab custom event
        const handleAvatarUpdate = () => loadAvatar();

        window.addEventListener('storage', handleStorage);
        window.addEventListener('user-avatar-updated', handleAvatarUpdate);

        return () => {
            window.removeEventListener('storage', handleStorage);
            window.removeEventListener('user-avatar-updated', handleAvatarUpdate);
        };
    }, []);

    return avatar;
}

/**
 * Save user avatar and dispatch update event
 */
export function saveUserAvatar(base64Url: string) {
    localStorage.setItem(USER_AVATAR_STORAGE_KEY, base64Url);
    window.dispatchEvent(new Event('user-avatar-updated'));
}
