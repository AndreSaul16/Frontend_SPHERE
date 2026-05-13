/**
 * Utilidades para exportar conversaciones de SPHERE.
 */
import type { Message, Agent } from '@/types';

export function exportAsMarkdown(
    messages: Message[],
    sessionTitle: string,
    agents: Agent[]
): string {
    const lines: string[] = [];
    const date = new Date().toLocaleDateString('es-ES', {
        year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });

    lines.push(`# ${sessionTitle}`);
    lines.push(`> Exportado desde SPHERE el ${date}`);
    lines.push('');
    lines.push('---');
    lines.push('');

    for (const msg of messages) {
        if (msg.role === 'system') {
            lines.push(`> *${msg.content}*`);
            lines.push('');
            continue;
        }

        const isUser = msg.role === 'user';
        const agent = msg.agentId ? agents.find(a => a.id === msg.agentId) : null;
        const senderName = isUser ? 'Usuario' : (agent?.name || msg.role || 'SPHERE');
        const timestamp = new Date(msg.timestamp).toLocaleTimeString('es-ES', {
            hour: '2-digit', minute: '2-digit'
        });

        lines.push(`### ${senderName} — ${timestamp}`);
        lines.push('');
        lines.push(msg.content);
        lines.push('');
        lines.push('---');
        lines.push('');
    }

    lines.push('');
    lines.push('*Powered by SPHERE Intelligence*');

    return lines.join('\n');
}

export function downloadAsFile(content: string, filename: string, mimeType: string = 'text/markdown') {
    const blob = new Blob([content], { type: `${mimeType};charset=utf-8` });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}
