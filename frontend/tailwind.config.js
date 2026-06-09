/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // "Midnight Protocol" Palette
                midnight: '#0A0A0F',      // Fondo Principal
                surface: '#121218',       // Cards / Sidebar
                surface_highlight: '#1A1A23', // Hover / Active

                // Acciones
                electric_cyan: '#00F0C8', // Acción Primaria
                luxury_purple: '#7B61FF', // Acento Secundario

                // Bubbles
                user_bubble: '#2A4D6E',
                ai_bubble: '#1C2B3A',

                // Texto
                text_primary: '#F0F0F5',
                text_secondary: '#8C8CA5',

                // Agentes (Identidad)
                agent_cto: '#00C1B3',
                agent_cfo: '#6B8AFD',
                agent_ceo: '#8A63D2',
                agent_cmo: '#E34A95',
            },
            fontFamily: {
                sans: ['Inter', 'SF Pro Display', 'system-ui', 'sans-serif'],
                mono: ['JetBrains Mono', 'SF Mono', 'monospace'], // Para cuando el CTO escupa código
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            }
        },
    },
    plugins: [],
}
