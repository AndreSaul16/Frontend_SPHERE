import { http, HttpResponse } from 'msw';

export const handlers = [
    // Mock para obtener agentes personalizados (Esquema Evolucionado)
    http.get('http://localhost:8000/api/v1/agents/', () => {
        return HttpResponse.json([
            {
                agent_id: 'custom-1',
                identity: {
                    name: 'Analista de Datos',
                    role: 'specialist',
                    color: '#3b82f6',
                    avatar_style: 'bar-chart'
                },
                brain_config: {
                    model: 'gpt-4o',
                    temperature: 0.7,
                    system_prompt: 'Eres un analista experto.'
                },
                owner_user_id: 'default_user',
                is_public: false
            }
        ]);
    }),

    // Mock para historial de sesión
    http.get('http://localhost:8000/api/v1/sessions/:id/history', () => {
        return HttpResponse.json({
            messages: [
                { type: 'human', content: 'Hola', additional_kwargs: {} },
                {
                    type: 'ai',
                    content: 'Aquí tienes el código: <sphere_artifact title="Sort" artifact_type="code" language="python">def sort(): pass</sphere_artifact>',
                    additional_kwargs: { agent_id: 'cto-1' }
                }
            ]
        });
    }),

    // Mock para crear sesión (Esquema Evolucionado)
    http.post('http://localhost:8000/api/v1/sessions/', () => {
        return HttpResponse.json({
            session_id: 'test-session-123',
            title: 'Sesión de Prueba',
            user_id: 'default_user',
            base_agent_id: 'CEO',
            visual_config: {
                name: 'Estrategia Master',
                color: '#8b5cf6'
            },
            context_files: [],
            enabled_tools: [],
            created_at: new Date().toISOString()
        });
    }),
];
