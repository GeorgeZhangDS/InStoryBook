/* =========================
   WebSocket Hook
========================= */

import { useEffect, useRef, useState, useCallback } from 'react';

/* =========================
   Types
========================= */

export type WebSocketEventType = 
    | 'session_ready'
    | 'agent_started'
    | 'chat_response'
    | 'finalizer_text'
    | 'finalizer_image'
    | 'pipeline_completed'
    | 'error';

export interface WebSocketMessage {
    event_id: string;
    type: WebSocketEventType;
    timestamp: number;
    session_id: string;
    data: Record<string, any>;
}

export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export type WebSocketEventHandler = (message: WebSocketMessage) => void;

/* =========================
   Hook Options
========================= */

import { getWebSocketUrl, API_CONFIG } from '../config/api';

interface UseWebSocketOptions {
    sessionId: string | null;
    onMessage?: WebSocketEventHandler;
    onError?: (error: Event) => void;
    onConnect?: () => void;
    onDisconnect?: () => void;
    autoReconnect?: boolean;
    reconnectInterval?: number;
    maxReconnectAttempts?: number;
}

/* =========================
   Hook Implementation
========================= */

export const useWebSocket = (options: UseWebSocketOptions) => {
    const {
        sessionId,
        onMessage,
        onError,
        onConnect,
        onDisconnect,
        autoReconnect = API_CONFIG.ws.autoReconnect,
        reconnectInterval = API_CONFIG.ws.reconnectInterval,
        maxReconnectAttempts = API_CONFIG.ws.maxReconnectAttempts,
    } = options;

    const [status, setStatus] = useState<WebSocketStatus>('disconnected');
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectAttemptsRef = useRef(0);
    const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
    const isManualCloseRef = useRef(false);

    /* =========================
       WebSocket URL Builder
    ========================= */

    const buildWebSocketUrl = useCallback((sid: string): string => {
        return getWebSocketUrl(sid);
    }, []);

    /* =========================
       Connect
    ========================= */

    const connect = useCallback(() => {
        if (!sessionId) {
            console.warn('Cannot connect: sessionId is null');
            return;
        }

        if (wsRef.current?.readyState === WebSocket.OPEN) {
            console.log('WebSocket already connected');
            return;
        }

        if (wsRef.current?.readyState === WebSocket.CONNECTING) {
            console.log('WebSocket connection in progress');
            return;
        }

        try {
            setStatus('connecting');
            const url = buildWebSocketUrl(sessionId);
            console.log(`Connecting to WebSocket: ${url}`);

            const ws = new WebSocket(url);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log('WebSocket connected');
                setStatus('connected');
                reconnectAttemptsRef.current = 0;
                onConnect?.();
            };

            ws.onmessage = (event) => {
                try {
                    const message: WebSocketMessage = JSON.parse(event.data);
                    console.log('Received message:', message.type, message.data);
                    onMessage?.(message);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                setStatus('error');
                onError?.(error);
            };

            ws.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason, 'wasClean:', event.wasClean);
                if (event.code !== 1000) {
                    console.error('WebSocket closed unexpectedly with code:', event.code);
                }
                setStatus('disconnected');
                onDisconnect?.();

                if (!isManualCloseRef.current && autoReconnect) {
                    if (reconnectAttemptsRef.current < maxReconnectAttempts) {
                        reconnectAttemptsRef.current++;
                        console.log(
                            `Reconnecting in ${reconnectInterval}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`
                        );
                        reconnectTimerRef.current = setTimeout(() => {
                            connect();
                        }, reconnectInterval);
                    } else {
                        console.error('Max reconnect attempts reached');
                    }
                }
            };
        } catch (error) {
            console.error('Error creating WebSocket:', error);
            setStatus('error');
        }
    }, [sessionId, buildWebSocketUrl, onMessage, onError, onConnect, onDisconnect, autoReconnect, reconnectInterval, maxReconnectAttempts]);

    /* =========================
       Disconnect
    ========================= */

    const disconnect = useCallback(() => {
        isManualCloseRef.current = true;
        
        if (reconnectTimerRef.current) {
            clearTimeout(reconnectTimerRef.current);
            reconnectTimerRef.current = null;
        }

        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }

        setStatus('disconnected');
    }, []);

    /* =========================
       Send Message
    ========================= */

    const sendMessage = useCallback((type: string, data: Record<string, any>) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            const message = JSON.stringify({ type, ...data });
            console.log('Sending message:', type, data);
            wsRef.current.send(message);
            return true;
        } else {
            console.warn('WebSocket is not connected. Cannot send message.');
            return false;
        }
    }, []);

    /* =========================
       Auto Connect Effect
    ========================= */

    useEffect(() => {
        if (!sessionId) {
            console.warn('useWebSocket: sessionId is null, cannot connect');
            return;
        }

        if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
            console.log('useWebSocket: WebSocket already connecting/connected, skipping');
            return;
        }

        console.log('useWebSocket: sessionId available, connecting...', sessionId);
        connect();

        return () => {
            console.log('useWebSocket: cleanup, disconnecting...');
            disconnect();
        };
    }, [sessionId]);


    /* =========================
       Return
    ========================= */

    return {
        status,
        connect,
        disconnect,
        sendMessage,
        isConnected: status === 'connected',
    };
};

