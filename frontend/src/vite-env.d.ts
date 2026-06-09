/// <reference types="vite/client" />

// Build-time injected globals from vite.config.ts define
declare const __GIT_COMMIT_SHA__: string;
declare const __BUILD_TIMESTAMP__: string;
declare const __VERSION__: string;
declare const __RAILWAY_SERVICE_NAME__: string;
