import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { SettingsPage } from '../../src/pages/SettingsPage';

// Mock all settings sub-components to avoid pulling in their dependencies
vi.mock('@/pages/settings/ProfileSettings', () => ({
    ProfileSettings: () => <div data-testid="profile-settings">Profile</div>,
}));
vi.mock('@/pages/settings/IntegrationsSettings', () => ({
    IntegrationsSettings: () => <div data-testid="integrations-settings">Integrations</div>,
}));
vi.mock('@/pages/settings/AgentOverridesSettings', () => ({
    AgentOverridesSettings: () => <div data-testid="agent-overrides-settings">Agents</div>,
}));
vi.mock('@/pages/settings/ContactsSettings', () => ({
    ContactsSettings: () => <div data-testid="contacts-settings">Contacts</div>,
}));
vi.mock('@/pages/settings/StorageSettings', () => ({
    StorageSettings: () => <div data-testid="storage-settings">Storage</div>,
}));
vi.mock('@/pages/settings/ServiceCredentialsSettings', () => ({
    ServiceCredentialsSettings: () => <div data-testid="service-credentials-settings">API Keys</div>,
}));
vi.mock('@/pages/settings/BoardMeetingSettings', () => ({
    BoardMeetingSettings: () => <div data-testid="board-meeting-settings">Board Meeting</div>,
}));

describe('SettingsPage — Scroll Fix (Task 2.4, SP-001)', () => {
    const renderSettingsPage = (section = 'profile') => {
        return render(
            <MemoryRouter initialEntries={[`/settings/${section}`]}>
                <SettingsPage />
            </MemoryRouter>
        );
    };

    it('root container allows vertical scroll (not overflow-hidden) — SP-001', () => {
        renderSettingsPage('profile');

        // The root div: <div className="flex flex-col h-full ... overflow-hidden">
        // After fix: overflow-hidden → overflow-y-auto
        const rootContainer = document.querySelector('.flex.flex-col.h-full');
        expect(rootContainer).not.toBeNull();

        const classes = rootContainer!.className;
        // Should allow vertical scrolling
        expect(classes).toContain('overflow-y-auto');
        // Should NOT clip overflow
        expect(classes).not.toContain('overflow-hidden');
    });

    it('renders scrollable content area when page loads — SP-001', () => {
        renderSettingsPage('profile');

        // The main content area should allow overflow scrolling
        const mainElement = screen.getByRole('main');
        expect(mainElement).toBeDefined();
        expect(mainElement.className).toContain('overflow-y-auto');
    });

    it('renders the header with back link', () => {
        renderSettingsPage('profile');

        expect(screen.getByText('Configuración')).toBeInTheDocument();
        // The back arrow link should exist
        const links = screen.getAllByRole('link');
        const backLink = links.find(link => link.getAttribute('href') === '/');
        expect(backLink).toBeDefined();
    });

    it('renders ProfileSettings for default /settings/profile route', () => {
        renderSettingsPage('profile');
        expect(screen.getByTestId('profile-settings')).toBeInTheDocument();
    });
});
