// Artifact Detector - Parses streaming content for artifacts
import { v4 as uuidv4 } from 'uuid';
import type { Artifact, ArtifactType } from '@/types/artifact';

interface DetectedArtifact {
    type: ArtifactType;
    content: string;
    language?: string;
    title: string;
}

// Regex patterns for detecting artifacts
const CODE_BLOCK_REGEX = /```(\w+)?\n([\s\S]*?)```/g;
const MERMAID_REGEX = /```mermaid\n([\s\S]*?)```/g;
const TABLE_REGEX = /\|(.+)\|\n\|[-:\s|]+\|\n((?:\|.+\|\n?)+)/g;

/**
 * Detects artifacts in a completed message content
 */
export function detectArtifacts(content: string, agentId?: string): Artifact[] {
    const artifacts: Artifact[] = [];
    const detected: DetectedArtifact[] = [];

    // Detect Mermaid diagrams (check first to avoid code block overlap)
    const mermaidMatches = content.matchAll(MERMAID_REGEX);
    for (const mMatch of mermaidMatches) {
        detected.push({
            type: 'mermaid',
            content: mMatch[1].trim(),
            title: 'Diagrama Mermaid',
        });
    }

    // Detect code blocks (excluding mermaid)
    const codeMatches = content.matchAll(CODE_BLOCK_REGEX);
    for (const cMatch of codeMatches) {
        const language = cMatch[1]?.toLowerCase();
        if (language === 'mermaid') continue; // Already handled

        detected.push({
            type: 'code',
            content: cMatch[2].trim(),
            language: language || 'text',
            title: language ? `Código ${language.toUpperCase()}` : 'Código',
        });
    }

    // Detect tables
    const tableMatches = content.matchAll(TABLE_REGEX);
    for (const tMatch of tableMatches) {
        const fullTable = tMatch[0].trim();
        detected.push({
            type: 'data_table',
            content: fullTable,
            title: 'Tabla de Datos',
        });
    }

    // Convert detected artifacts to full Artifact objects
    for (const d of detected) {
        artifacts.push({
            id: uuidv4(),
            type: d.type,
            title: d.title,
            content: d.content,
            language: d.language,
            agentId,
            createdAt: new Date(),
        });
    }

    return artifacts;
}

/**
 * Checks if content has any detectable artifacts
 */
export function hasArtifacts(content: string): boolean {
    return CODE_BLOCK_REGEX.test(content) || TABLE_REGEX.test(content);
}
