import '@testing-library/jest-dom';
import { beforeAll, afterEach, afterAll, vi } from 'vitest';
import { setupServer } from 'msw/node';
import { handlers } from './mocks/handlers';

export const server = setupServer(...handlers);

// Establecer mocks de API antes de todos los tests
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));

// Resetear handlers después de cada test para evitar interferencias
afterEach(() => server.resetHandlers());

// Limpiar después de todos los tests
afterAll(() => server.close());

// Mock de DOM APIs que JSDOM no soporta
window.HTMLElement.prototype.scrollIntoView = vi.fn();
window.HTMLElement.prototype.scrollTo = vi.fn();
