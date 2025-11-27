import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useWebSocket } from '@/hooks/useWebSocket';

describe('WebSocket Reconnection Tests', () => {
    let mockWebSocket: any;
    let originalWebSocket: typeof WebSocket;

    beforeEach(() => {
        originalWebSocket = global.WebSocket;
        mockWebSocket = {
            CONNECTING: 0,
            OPEN: 1,
            CLOSING: 2,
            CLOSED: 3,
            readyState: 0,
            sentMessages: [] as string[],
            send: vi.fn(),
            close: vi.fn(),
            addEventListener: vi.fn(),
            removeEventListener: vi.fn(),
        };
    });

    afterEach(() => {
        global.WebSocket = originalWebSocket;
        vi.clearAllMocks();
    });

    it('should reconnect after unexpected disconnect', async () => {
        let connectCount = 0;
        (global as any).WebSocket = vi.fn((url: string) => {
            connectCount++;
            const ws = {
                ...mockWebSocket,
                url,
                readyState: mockWebSocket.CONNECTING,
            };

            setTimeout(() => {
                ws.readyState = mockWebSocket.OPEN;
                if (ws.onopen) ws.onopen(new Event('open'));
            }, 10);

            return ws;
        });

        const { result } = renderHook(() =>
            useWebSocket({
                sessionId: 'test-session',
                autoReconnect: true,
                maxReconnectAttempts: 3,
                reconnectInterval: 50,
            })
        );

        await waitFor(() => {
            expect(result.current.isConnected).toBe(true);
        });

        // Simulate unexpected disconnect
        const wsInstance = (global as any).WebSocket.mock.results[0].value;
        wsInstance.readyState = mockWebSocket.CLOSED;
        if (wsInstance.onclose) {
            wsInstance.onclose({
                code: 1006,
                reason: 'Connection lost',
                wasClean: false,
            } as CloseEvent);
        }

        await waitFor(() => {
            expect(connectCount).toBeGreaterThan(1);
        }, { timeout: 1000 });
    });

    it('should not reconnect after manual disconnect', async () => {
        (global as any).WebSocket = vi.fn(() => {
            const ws = {
                ...mockWebSocket,
                readyState: mockWebSocket.CONNECTING,
            };
            setTimeout(() => {
                ws.readyState = mockWebSocket.OPEN;
                if (ws.onopen) ws.onopen(new Event('open'));
            }, 10);
            return ws;
        });

        const { result } = renderHook(() =>
            useWebSocket({
                sessionId: 'test-session',
                autoReconnect: true,
            })
        );

        await waitFor(() => {
            expect(result.current.isConnected).toBe(true);
        });

        const initialCallCount = (global as any).WebSocket.mock.calls.length;
        result.current.disconnect();

        await waitFor(() => {
            expect(result.current.isConnected).toBe(false);
        });

        // Wait to ensure no reconnection
        await new Promise(resolve => setTimeout(resolve, 200));
        expect((global as any).WebSocket.mock.calls.length).toBe(initialCallCount);
    });

    it('should respect max reconnect attempts', async () => {
        const maxAttempts = 2;
        let attemptCount = 0;

        (global as any).WebSocket = vi.fn(() => {
            attemptCount++;
            const ws = {
                ...mockWebSocket,
                readyState: mockWebSocket.CONNECTING,
            };
            
            setTimeout(() => {
                ws.readyState = mockWebSocket.CLOSED;
                if (ws.onclose) {
                    ws.onclose({
                        code: 1006,
                        reason: 'Connection failed',
                        wasClean: false,
                    } as CloseEvent);
                }
            }, 10);
            
            return ws;
        });

        renderHook(() =>
            useWebSocket({
                sessionId: 'test-session',
                autoReconnect: true,
                maxReconnectAttempts: maxAttempts,
                reconnectInterval: 50,
            })
        );

        await waitFor(() => {
            expect(attemptCount).toBe(maxAttempts + 1);
        }, { timeout: 1000 });
    });

    it('should handle connection errors during reconnection', async () => {
        let callCount = 0;
        (global as any).WebSocket = vi.fn(() => {
            callCount++;
            const ws = {
                ...mockWebSocket,
                readyState: mockWebSocket.CONNECTING,
            };
            
            setTimeout(() => {
                if (callCount === 1) {
                    // First attempt: connect then disconnect
                    ws.readyState = mockWebSocket.OPEN;
                    if (ws.onopen) ws.onopen(new Event('open'));
                    setTimeout(() => {
                        ws.readyState = mockWebSocket.CLOSED;
                        if (ws.onclose) {
                            ws.onclose({
                                code: 1006,
                                wasClean: false,
                            } as CloseEvent);
                        }
                    }, 20);
                } else {
                    // Subsequent attempts: error
                    if (ws.onerror) ws.onerror(new Event('error'));
                }
            }, 10);
            
            return ws;
        });

        const onError = vi.fn();
        renderHook(() =>
            useWebSocket({
                sessionId: 'test-session',
                autoReconnect: true,
                maxReconnectAttempts: 2,
                reconnectInterval: 50,
                onError,
            })
        );

        await waitFor(() => {
            expect(callCount).toBeGreaterThan(1);
        }, { timeout: 500 });
    });
});

