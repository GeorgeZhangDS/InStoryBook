/* =========================
   API Configuration
========================= */

/* =========================
   Environment Variables
========================= */

export const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/ws';
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

/* =========================
   WebSocket URL Helper
========================= */

export const getWebSocketUrl = (sessionId: string): string => {
    return `${WS_BASE_URL}/${sessionId}`;
};

/* =========================
   API Endpoints
========================= */

export const API_ENDPOINTS = {
    websocket: (sessionId: string) => getWebSocketUrl(sessionId),
    health: `${API_BASE_URL.replace('/api/v1', '')}/health`,
    docs: `${API_BASE_URL.replace('/api/v1', '')}/docs`,
} as const;

/* =========================
   Configuration
========================= */

export const API_CONFIG = {
    ws: {
        reconnectInterval: 3000,
        maxReconnectAttempts: 5,
        autoReconnect: true,
    },
    timeout: 30000,
} as const;

