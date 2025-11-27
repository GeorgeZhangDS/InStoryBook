import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useWebSocket, WebSocketMessage } from '@/hooks/useWebSocket';

describe('useWebSocket Hook', () => {
    let mockWebSocket: any;
    let originalWebSocket: typeof WebSocket;

    beforeEach(() => {
        // Store original WebSocket
        originalWebSocket = global.WebSocket;
        
        // Create mock WebSocket
        mockWebSocket = {
            CONNECTING: 0,
            OPEN: 1,
            CLOSING: 2,
            CLOSED: 3,
            readyState: 0,
            url: '',
            onopen: null,
            onclose: null,
            onmessage: null,
            onerror: null,
            sentMessages: [] as string[],
            send: vi.fn((data: string) => {
                mockWebSocket.sentMessages.push(data);
            }),
            close: vi.fn((code?: number, reason?: string) => {
                mockWebSocket.readyState = mockWebSocket.CLOSED;
                if (mockWebSocket.onclose) {
                    mockWebSocket.onclose({ code: code || 1000, reason: reason || '', wasClean: true } as CloseEvent);
                }
            }),
            addEventListener: vi.fn(),
            removeEventListener: vi.fn(),
            dispatchEvent: vi.fn(),
        };

        // Replace global WebSocket
        (global as any).WebSocket = vi.fn((url: string) => {
            mockWebSocket.url = url;
            mockWebSocket.readyState = mockWebSocket.CONNECTING;
            
            // Simulate connection
            setTimeout(() => {
                mockWebSocket.readyState = mockWebSocket.OPEN;
                if (mockWebSocket.onopen) {
                    mockWebSocket.onopen(new Event('open'));
                }
            }, 10);
            
            return mockWebSocket;
        });
    });

    afterEach(() => {
        // Restore original WebSocket
        global.WebSocket = originalWebSocket;
        vi.clearAllMocks();
    });

    describe('Connection', () => {
        it('should connect when sessionId is provided', async () => {
            const onConnect = vi.fn();
            const { result } = renderHook(() =>
                useWebSocket({
                    sessionId: 'test-session-123',
                    onConnect,
                })
            );

            await waitFor(() => {
                expect(result.current.isConnected).toBe(true);
            }, { timeout: 1000 });

            expect(onConnect).toHaveBeenCalled();
            expect(result.current.status).toBe('connected');
        });

        it('should not connect when sessionId is null', () => {
            const { result } = renderHook(() =>
                useWebSocket({
                    sessionId: null,
                })
            );

            expect(result.current.isConnected).toBe(false);
            expect(result.current.status).toBe('disconnected');
        });

        it('should handle connection errors', async () => {
            const onError = vi.fn();
            (global as any).WebSocket = vi.fn(() => {
                const ws = mockWebSocket;
                setTimeout(() => {
                    if (ws.onerror) {
                        ws.onerror(new Event('error'));
                    }
                }, 10);
                return ws;
            });

            const { result } = renderHook(() =>
                useWebSocket({
                    sessionId: 'test-session',
                    onError,
                })
            );

            await waitFor(() => {
                expect(onError).toHaveBeenCalled();
            });

            expect(result.current.status).toBe('error');
        });

        it('should disconnect when sessionId changes to null', async () => {
            const onDisconnect = vi.fn();
            const { result, rerender } = renderHook(
                ({ sessionId }) =>
                    useWebSocket({
                        sessionId,
                        onDisconnect,
                    }),
                { initialProps: { sessionId: 'test-session' } }
            );

            await waitFor(() => {
                expect(result.current.isConnected).toBe(true);
            });

            rerender({ sessionId: null });

            await waitFor(() => {
                expect(onDisconnect).toHaveBeenCalled();
            });
        });
    });

    describe('Message Handling', () => {
        it('should receive and handle messages', async () => {
            const onMessage = vi.fn();
            const testMessage: WebSocketMessage = {
                event_id: 'event-123',
                type: 'session_ready',
                timestamp: Date.now() / 1000,
                session_id: 'test-session',
                data: { status: 'ready' },
            };

            renderHook(() =>
                useWebSocket({
                    sessionId: 'test-session',
                    onMessage,
                })
            );

            await waitFor(() => {
                expect(mockWebSocket.readyState).toBe(mockWebSocket.OPEN);
            });

            // Simulate receiving a message
            if (mockWebSocket.onmessage) {
                mockWebSocket.onmessage({
                    data: JSON.stringify(testMessage),
                } as MessageEvent);
            }

            await waitFor(() => {
                expect(onMessage).toHaveBeenCalledWith(testMessage);
            });
        });

        it('should handle invalid JSON messages gracefully', async () => {
            const onMessage = vi.fn();
            const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

            renderHook(() =>
                useWebSocket({
                    sessionId: 'test-session',
                    onMessage,
                })
            );

            await waitFor(() => {
                expect(mockWebSocket.readyState).toBe(mockWebSocket.OPEN);
            });

            // Simulate receiving invalid JSON
            if (mockWebSocket.onmessage) {
                mockWebSocket.onmessage({
                    data: 'invalid json',
                } as MessageEvent);
            }

            await waitFor(() => {
                expect(consoleError).toHaveBeenCalled();
            });

            expect(onMessage).not.toHaveBeenCalled();
            consoleError.mockRestore();
        });

        it('should handle different message types', async () => {
            const onMessage = vi.fn();
            const messageTypes: WebSocketMessage['type'][] = [
                'session_ready',
                'agent_started',
                'chat_response',
                'finalizer_text',
                'finalizer_image',
                'pipeline_completed',
                'error',
            ];

            renderHook(() =>
                useWebSocket({
                    sessionId: 'test-session',
                    onMessage,
                })
            );

            await waitFor(() => {
                expect(mockWebSocket.readyState).toBe(mockWebSocket.OPEN);
            });

            messageTypes.forEach((type, index) => {
                const message: WebSocketMessage = {
                    event_id: `event-${index}`,
                    type,
                    timestamp: Date.now() / 1000,
                    session_id: 'test-session',
                    data: { test: 'data' },
                };

                if (mockWebSocket.onmessage) {
                    mockWebSocket.onmessage({
                        data: JSON.stringify(message),
                    } as MessageEvent);
                }
            });

            await waitFor(() => {
                expect(onMessage).toHaveBeenCalledTimes(messageTypes.length);
            });
        });
    });

    describe('Send Message', () => {
        it('should send messages when connected', async () => {
            const { result } = renderHook(() =>
                useWebSocket({
                    sessionId: 'test-session',
                })
            );

            await waitFor(() => {
                expect(result.current.isConnected).toBe(true);
            });

            const success = result.current.sendMessage('message', { theme: 'test story' });

            expect(success).toBe(true);
            expect(mockWebSocket.send).toHaveBeenCalled();
            expect(mockWebSocket.sentMessages.length).toBeGreaterThan(0);
            
            const sentData = JSON.parse(mockWebSocket.sentMessages[0]);
            expect(sentData.type).toBe('message');
            expect(sentData.theme).toBe('test story');
        });

        it('should not send messages when not connected', () => {
            const { result } = renderHook(() =>
                useWebSocket({
                    sessionId: null,
                })
            );

            const success = result.current.sendMessage('message', { theme: 'test' });

            expect(success).toBe(false);
            expect(mockWebSocket.send).not.toHaveBeenCalled();
        });

        it('should not send messages when connecting', () => {
            mockWebSocket.readyState = mockWebSocket.CONNECTING;
            
            const { result } = renderHook(() =>
                useWebSocket({
                    sessionId: 'test-session',
                })
            );

            const success = result.current.sendMessage('message', { theme: 'test' });

            // Should fail because not yet connected
            expect(success).toBe(false);
        });
    });

    describe('Reconnection', () => {
        it('should attempt to reconnect on unexpected close', async () => {
            const maxAttempts = 3;
            const reconnectInterval = 100;

            const { result } = renderHook(() =>
                useWebSocket({
                    sessionId: 'test-session',
                    autoReconnect: true,
                    maxReconnectAttempts: maxAttempts,
                    reconnectInterval,
                })
            );

            await waitFor(() => {
                expect(result.current.isConnected).toBe(true);
            });

            // Simulate unexpected close
            mockWebSocket.readyState = mockWebSocket.CLOSED;
            if (mockWebSocket.onclose) {
                mockWebSocket.onclose({
                    code: 1006,
                    reason: 'Connection lost',
                    wasClean: false,
                } as CloseEvent);
            }

            // Wait for reconnection attempts
            await waitFor(() => {
                expect((global as any).WebSocket).toHaveBeenCalledTimes(maxAttempts + 1);
            }, { timeout: 2000 });
        });

        it('should not reconnect when manually closed', async () => {
            const { result } = renderHook(() =>
                useWebSocket({
                    sessionId: 'test-session',
                    autoReconnect: true,
                })
            );

            await waitFor(() => {
                expect(result.current.isConnected).toBe(true);
            });

            result.current.disconnect();

            await waitFor(() => {
                expect(mockWebSocket.close).toHaveBeenCalled();
            });

            // Should not attempt to reconnect after manual disconnect
            const callCount = (global as any).WebSocket.mock.calls.length;
            await new Promise(resolve => setTimeout(resolve, 500));
            expect((global as any).WebSocket.mock.calls.length).toBe(callCount);
        });

        it('should respect max reconnect attempts', async () => {
            const maxAttempts = 2;
            const reconnectInterval = 50;

            renderHook(() =>
                useWebSocket({
                    sessionId: 'test-session',
                    autoReconnect: true,
                    maxReconnectAttempts: maxAttempts,
                    reconnectInterval,
                })
            );

            await waitFor(() => {
                expect(mockWebSocket.readyState).toBe(mockWebSocket.OPEN);
            });

            // Simulate connection failures
            (global as any).WebSocket = vi.fn(() => {
                const ws = { ...mockWebSocket };
                setTimeout(() => {
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

            // Trigger close
            if (mockWebSocket.onclose) {
                mockWebSocket.onclose({
                    code: 1006,
                    reason: 'Connection lost',
                    wasClean: false,
                } as CloseEvent);
            }

            await waitFor(() => {
                expect((global as any).WebSocket).toHaveBeenCalledTimes(maxAttempts + 1);
            }, { timeout: 1000 });
        });
    });

    describe('Status Management', () => {
        it('should update status correctly through connection lifecycle', async () => {
            const { result } = renderHook(() =>
                useWebSocket({
                    sessionId: 'test-session',
                })
            );

            // Initially disconnected
            expect(result.current.status).toBe('disconnected');

            // Connecting
            await waitFor(() => {
                expect(result.current.status).toBe('connecting');
            }, { timeout: 50 });

            // Connected
            await waitFor(() => {
                expect(result.current.status).toBe('connected');
            }, { timeout: 1000 });
        });

        it('should return correct isConnected value', async () => {
            const { result } = renderHook(() =>
                useWebSocket({
                    sessionId: 'test-session',
                })
            );

            expect(result.current.isConnected).toBe(false);

            await waitFor(() => {
                expect(result.current.isConnected).toBe(true);
            });
        });
    });

    describe('Manual Control', () => {
        it('should allow manual connect', async () => {
            const { result } = renderHook(() =>
                useWebSocket({
                    sessionId: 'test-session',
                })
            );

            await waitFor(() => {
                expect(result.current.isConnected).toBe(true);
            });

            result.current.disconnect();

            await waitFor(() => {
                expect(result.current.isConnected).toBe(false);
            });

            result.current.connect();

            await waitFor(() => {
                expect(result.current.isConnected).toBe(true);
            });
        });

        it('should prevent multiple simultaneous connections', async () => {
            const { result } = renderHook(() =>
                useWebSocket({
                    sessionId: 'test-session',
                })
            );

            await waitFor(() => {
                expect(result.current.isConnected).toBe(true);
            });

            const initialCallCount = (global as any).WebSocket.mock.calls.length;

            // Try to connect again
            result.current.connect();
            result.current.connect();
            result.current.connect();

            await new Promise(resolve => setTimeout(resolve, 100));

            // Should not create new connections if already connected
            expect((global as any).WebSocket.mock.calls.length).toBe(initialCallCount);
        });
    });
});

