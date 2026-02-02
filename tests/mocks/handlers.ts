import { http, HttpResponse } from 'msw';

export const handlers = [
    // Mock para obtener agentes personalizados
    http.get('http://localhost:8000/api/v1/agents/', () => {
        return HttpResponse.json([
            {
                id: 'custom-1',
                name: 'Analista de Datos',
                description: 'Test',
                system_prompt: 'Test',
                role: 'specialist',
                avatar: '📊',
                color: 'text-blue-500'
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

    // Mock para crear sesión
    http.post('http://localhost:8000/api/v1/sessions/', () => {
        return HttpResponse.json({
            session_id: 'test-session-123',
            title: 'Sesión de Prueba'
        });
    }),
];
