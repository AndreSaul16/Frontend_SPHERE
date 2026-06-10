/**
 * Limpia todo el estado específico del usuario (A6).
 *
 * Se llama al expirar/invalidarse la sesión y al cerrar sesión, ANTES de
 * cualquier redirect. Evita que en un navegador compartido el siguiente usuario
 * vea —aunque sea un instante— mensajes, agentes o saldo de la cuenta anterior.
 */
import { useChatStore } from '../store/useChatStore';
import { useBillingStore } from '../store/useBillingStore';

export function clearUserStores(): void {
  try {
    useChatStore.getState().resetState();
  } catch {
    /* no romper el flujo de logout por un fallo de reset */
  }
  try {
    useBillingStore.getState().reset();
  } catch {
    /* idem */
  }
}
