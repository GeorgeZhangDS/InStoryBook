import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from '@/stores/chatStore';

describe('WebSocket Message Handling', () => {
    beforeEach(() => {
        useChatStore.getState().reset();
    });

    describe('Message Format Validation', () => {
        it('should handle messages with all required fields', () => {
            const message = {
                event_id: 'event-123',
                type: 'agent_started',
                timestamp: Date.now() / 1000,
                session_id: 'test-session',
                data: { agent: 'planner', status: 'running' },
            };

            useChatStore.getState().handleWebSocketEvent(message.type, message.data, message.timestamp);

            const logs = useChatStore.getState().logs;
            expect(logs.length).toBeGreaterThan(0);
        });

        it('should handle messages with missing optional fields', () => {
            useChatStore.getState().handleWebSocketEvent('agent_started', {
                agent: 'planner',
            });

            const logs = useChatStore.getState().logs;
            expect(logs.some(log => log.message.includes('planner started'))).toBe(true);
        });

        it('should handle messages with timestamp', () => {
            const timestamp = 1234567890;
            useChatStore.getState().handleWebSocketEvent('session_ready', {}, timestamp);

            const logs = useChatStore.getState().logs;
            const log = logs.find(l => l.message.includes('WebSocket connected'));
            expect(log?.timestamp).toBeDefined();
        });
    });

    describe('Event Type Handling', () => {
        it('should handle unknown event types gracefully', () => {
            expect(() => {
                useChatStore.getState().handleWebSocketEvent('unknown_event', {});
            }).not.toThrow();
        });

        it('should handle empty data objects', () => {
            expect(() => {
                useChatStore.getState().handleWebSocketEvent('session_ready', {});
                useChatStore.getState().handleWebSocketEvent('pipeline_completed', {});
            }).not.toThrow();
        });

        it('should handle null/undefined data gracefully', () => {
            expect(() => {
                useChatStore.getState().handleWebSocketEvent('session_ready', null as any);
                useChatStore.getState().handleWebSocketEvent('pipeline_completed', undefined as any);
            }).not.toThrow();
        });
    });

    describe('Chapter Data Handling', () => {
        it('should handle chapters with different field names', () => {
            const chaptersWithContent = [
                { chapter_id: 1, title: 'Ch1', content: 'Text 1' },
            ];
            const chaptersWithText = [
                { chapter_id: 2, title: 'Ch2', text: 'Text 2' },
            ];

            useChatStore.getState().handleWebSocketEvent('finalizer_text', {
                chapters: chaptersWithContent,
            });

            useChatStore.getState().handleWebSocketEvent('finalizer_text', {
                chapters: chaptersWithText,
            });

            const messages = useChatStore.getState().messages;
            expect(messages.length).toBe(2);
        });

        it('should handle chapters with missing fields', () => {
            const incompleteChapters = [
                { chapter_id: 1 },
                { chapter_id: 2, title: 'Chapter 2' },
            ];

            useChatStore.getState().handleWebSocketEvent('finalizer_text', {
                chapters: incompleteChapters,
            });

            const messages = useChatStore.getState().messages;
            expect(messages.length).toBe(1);
            expect(messages[0].storyChapters?.length).toBe(2);
        });

        it('should handle image URLs in different formats', () => {
            // First add text
            useChatStore.getState().handleWebSocketEvent('finalizer_text', {
                chapters: [
                    { chapter_id: 1, title: 'Ch1', text: 'Text 1' },
                ],
            });

            // Then add images with 'image' field
            useChatStore.getState().handleWebSocketEvent('finalizer_image', {
                chapters: [
                    { chapter_id: 1, image: 'https://example.com/img.jpg' },
                ],
            });

            const messages = useChatStore.getState().messages;
            const storyMessage = messages.find(m => m.storyChapters);
            expect(storyMessage?.storyChapters?.[0].image_url).toBe('https://example.com/img.jpg');
        });
    });

    describe('Agent Step Updates', () => {
        it('should update steps correctly for different agents', () => {
            const agents = ['planner', 'writer', 'illustrator', 'chat'];
            
            agents.forEach(agent => {
                useChatStore.getState().reset();
                useChatStore.getState().handleWebSocketEvent('agent_started', {
                    agent,
                    status: 'running',
                });
                
                const steps = useChatStore.getState().agentSteps;
                expect(steps.length).toBeGreaterThan(0);
            });
        });

        it('should handle multiple step updates in sequence', () => {
            useChatStore.getState().handleWebSocketEvent('agent_started', {
                agent: 'planner',
            });
            
            useChatStore.getState().handleWebSocketEvent('agent_completed', {
                agent: 'planner',
            });
            
            useChatStore.getState().handleWebSocketEvent('agent_started', {
                agent: 'writer',
            });
            
            const steps = useChatStore.getState().agentSteps;
            expect(steps.find(s => s.id === 'planning')?.status).toBe('completed');
            expect(steps.find(s => s.id === 'writing')?.status).toBe('active');
        });
    });

    describe('Workflow Branch Management', () => {
        it('should set workflow branch to story-graph for planner', () => {
            useChatStore.getState().handleWebSocketEvent('agent_started', {
                agent: 'planner',
            });
            
            expect(useChatStore.getState().workflowBranch).toBe('story-graph');
        });

        it('should set workflow branch to chat for chat agent', () => {
            useChatStore.getState().handleWebSocketEvent('agent_started', {
                agent: 'chat',
            });
            
            expect(useChatStore.getState().workflowBranch).toBe('chat');
        });

        it('should maintain workflow branch through pipeline', () => {
            useChatStore.getState().handleWebSocketEvent('agent_started', {
                agent: 'planner',
            });
            
            expect(useChatStore.getState().workflowBranch).toBe('story-graph');
            
            useChatStore.getState().handleWebSocketEvent('agent_completed', {
                agent: 'planner',
            });
            
            expect(useChatStore.getState().workflowBranch).toBe('story-graph');
        });
    });

    describe('Typewriter Flag Management', () => {
        it('should set needsTypewriter for chat responses', () => {
            useChatStore.getState().handleWebSocketEvent('chat_response', {
                response: 'Hello!',
            });
            
            const messages = useChatStore.getState().messages;
            expect(messages[0].needsTypewriter).toBe(true);
        });

        it('should set needsTypewriter for finalizer_text', () => {
            useChatStore.getState().handleWebSocketEvent('finalizer_text', {
                chapters: [
                    { chapter_id: 1, title: 'Ch1', content: 'Text 1', text: 'Text 1' },
                ],
            });
            
            const messages = useChatStore.getState().messages;
            expect(messages[0].needsTypewriter).toBe(true);
        });
    });

    describe('State Consistency', () => {
        it('should maintain consistent state after multiple events', () => {
            // Simulate a complete workflow
            useChatStore.getState().handleWebSocketEvent('session_ready', {});
            useChatStore.getState().handleWebSocketEvent('agent_started', { agent: 'planner' });
            useChatStore.getState().handleWebSocketEvent('agent_completed', { agent: 'planner' });
            useChatStore.getState().handleWebSocketEvent('agent_started', { agent: 'writer' });
            
            const state = useChatStore.getState();
            expect(state.wsConnected).toBe(true);
            expect(state.workflowBranch).toBe('story-graph');
            expect(state.agentSteps.length).toBeGreaterThan(0);
        });

        it('should handle rapid state changes', () => {
            const events = [
                ['agent_started', { agent: 'planner' }],
                ['agent_completed', { agent: 'planner' }],
                ['agent_started', { agent: 'writer' }],
                ['agent_completed', { agent: 'writer_1', chapter_id: 1 }],
                ['agent_completed', { agent: 'writer_2', chapter_id: 2 }],
                ['agent_completed', { agent: 'writer_3', chapter_id: 3 }],
                ['agent_completed', { agent: 'writer_4', chapter_id: 4 }],
                ['agent_completed', { agent: 'writer' }],
            ];

            events.forEach(([type, data]) => {
                useChatStore.getState().handleWebSocketEvent(type as string, data);
            });

            const steps = useChatStore.getState().agentSteps;
            expect(steps.find(s => s.id === 'planning')?.status).toBe('completed');
            expect(steps.find(s => s.id === 'writing')?.status).toBe('completed');
        });
    });
});

