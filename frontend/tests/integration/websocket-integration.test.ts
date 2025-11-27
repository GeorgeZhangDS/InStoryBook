import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useChatStore } from '@/stores/chatStore';

describe('WebSocket Integration Tests', () => {
    beforeEach(() => {
        useChatStore.getState().reset();
    });

    describe('Complete Story Generation Flow', () => {
        it('should handle complete story generation workflow', () => {
            // 1. Session ready
            useChatStore.getState().handleWebSocketEvent('session_ready', {});
            expect(useChatStore.getState().wsConnected).toBe(true);

            // 2. Planner started
            useChatStore.getState().handleWebSocketEvent('agent_started', {
                agent: 'planner',
                status: 'running',
            });
            expect(useChatStore.getState().workflowBranch).toBe('story-graph');
            expect(useChatStore.getState().agentSteps.find(s => s.id === 'planning')?.status).toBe('active');

            // 3. Planner completed
            useChatStore.getState().handleWebSocketEvent('agent_completed', {
                agent: 'planner',
                status: 'completed',
            });
            expect(useChatStore.getState().agentSteps.find(s => s.id === 'planning')?.status).toBe('completed');

            // 4. Writer started
            useChatStore.getState().handleWebSocketEvent('agent_started', {
                agent: 'writer',
                status: 'running',
            });
            expect(useChatStore.getState().agentSteps.find(s => s.id === 'writing')?.status).toBe('active');

            // 5. Individual writers completed
            for (let i = 1; i <= 4; i++) {
                useChatStore.getState().handleWebSocketEvent('agent_completed', {
                    agent: `writer_${i}`,
                    chapter_id: i,
                    status: 'completed',
                });
            }

            // 6. All writers completed
            useChatStore.getState().handleWebSocketEvent('agent_completed', {
                agent: 'writer',
                status: 'completed',
            });
            expect(useChatStore.getState().agentSteps.find(s => s.id === 'writing')?.status).toBe('completed');

            // 7. Finalizer text
            const chapters = [
                { chapter_id: 1, title: 'Chapter 1', content: 'Text 1', text: 'Text 1' },
                { chapter_id: 2, title: 'Chapter 2', content: 'Text 2', text: 'Text 2' },
                { chapter_id: 3, title: 'Chapter 3', content: 'Text 3', text: 'Text 3' },
                { chapter_id: 4, title: 'Chapter 4', content: 'Text 4', text: 'Text 4' },
            ];
            useChatStore.getState().handleWebSocketEvent('finalizer_text', { chapters });
            
            const messages = useChatStore.getState().messages;
            expect(messages.length).toBe(1);
            expect(messages[0].storyChapters?.length).toBe(4);

            // 8. Illustrator started
            useChatStore.getState().handleWebSocketEvent('agent_started', {
                agent: 'illustrator',
                status: 'running',
            });
            expect(useChatStore.getState().agentSteps.find(s => s.id === 'illustrating')?.status).toBe('active');

            // 9. Individual illustrators completed
            for (let i = 1; i <= 4; i++) {
                useChatStore.getState().handleWebSocketEvent('agent_completed', {
                    agent: `illustrator_${i}`,
                    chapter_id: i,
                    status: 'completed',
                });
            }

            // 10. All illustrators completed
            useChatStore.getState().handleWebSocketEvent('agent_completed', {
                agent: 'illustrator',
                status: 'completed',
            });
            expect(useChatStore.getState().agentSteps.find(s => s.id === 'illustrating')?.status).toBe('completed');

            // 11. Finalizer image
            const imageChapters = [
                { chapter_id: 1, image: 'https://example.com/img1.jpg' },
                { chapter_id: 2, image: 'https://example.com/img2.jpg' },
                { chapter_id: 3, image: 'https://example.com/img3.jpg' },
                { chapter_id: 4, image: 'https://example.com/img4.jpg' },
            ];
            useChatStore.getState().handleWebSocketEvent('finalizer_image', { chapters: imageChapters });

            // 12. Pipeline completed
            useChatStore.getState().handleWebSocketEvent('pipeline_completed', { status: 'completed' });
            expect(useChatStore.getState().isGenerating).toBe(false);

            // Verify final state
            const finalMessages = useChatStore.getState().messages;
            const storyMessage = finalMessages.find(m => m.storyChapters);
            expect(storyMessage?.storyChapters?.every(ch => ch.image_url)).toBe(true);
        });
    });

    describe('Complete Chat Flow', () => {
        it('should handle complete chat workflow', () => {
            // 1. Session ready
            useChatStore.getState().handleWebSocketEvent('session_ready', {});
            
            // 2. Chat started
            useChatStore.getState().handleWebSocketEvent('agent_started', {
                agent: 'chat',
                status: 'running',
            });
            expect(useChatStore.getState().workflowBranch).toBe('chat');
            expect(useChatStore.getState().agentSteps.find(s => s.id === 'chat')?.status).toBe('active');

            // 3. Chat response
            useChatStore.getState().handleWebSocketEvent('chat_response', {
                response: 'Hello! How can I help you?',
            });
            
            const messages = useChatStore.getState().messages;
            expect(messages.length).toBe(1);
            expect(messages[0].content).toBe('Hello! How can I help you?');
            expect(messages[0].needsTypewriter).toBe(true);

            // 4. Chat completed
            useChatStore.getState().handleWebSocketEvent('agent_completed', {
                agent: 'chat',
                status: 'completed',
            });
            expect(useChatStore.getState().agentSteps.find(s => s.id === 'chat')?.status).toBe('completed');

            // 5. Pipeline completed
            useChatStore.getState().handleWebSocketEvent('pipeline_completed', { status: 'completed' });
            expect(useChatStore.getState().isGenerating).toBe(false);
        });
    });

    describe('Error Handling', () => {
        it('should handle errors gracefully', () => {
            useChatStore.getState().setIsGenerating(true);
            
            useChatStore.getState().handleWebSocketEvent('error', {
                agent: 'story_generation',
                error: 'Test error',
            });
            
            expect(useChatStore.getState().isGenerating).toBe(false);
            const logs = useChatStore.getState().logs;
            expect(logs.some(log => log.type === 'error' && log.message.includes('Test error'))).toBe(true);
        });

        it('should continue workflow after non-fatal errors', () => {
            useChatStore.getState().handleWebSocketEvent('agent_started', {
                agent: 'planner',
                status: 'running',
            });
            
            useChatStore.getState().handleWebSocketEvent('error', {
                agent: 'planner',
                error: 'Minor error',
            });
            
            // Should still be able to continue
            useChatStore.getState().handleWebSocketEvent('agent_completed', {
                agent: 'planner',
                status: 'completed',
            });
            
            expect(useChatStore.getState().agentSteps.find(s => s.id === 'planning')?.status).toBe('completed');
        });
    });

    describe('State Persistence', () => {
        it('should maintain state across multiple events', () => {
            const sessionId = useChatStore.getState().getOrCreateSessionId();
            
            useChatStore.getState().addMessage('user', 'First message');
            useChatStore.getState().handleWebSocketEvent('agent_started', {
                agent: 'planner',
            });
            useChatStore.getState().addMessage('assistant', 'Response');
            
            expect(useChatStore.getState().sessionId).toBe(sessionId);
            expect(useChatStore.getState().messages.length).toBe(2);
            expect(useChatStore.getState().agentSteps.length).toBeGreaterThan(0);
        });
    });

    describe('Concurrent Events', () => {
        it('should handle rapid sequential events', () => {
            // Simulate rapid events
            for (let i = 1; i <= 4; i++) {
                useChatStore.getState().handleWebSocketEvent('agent_completed', {
                    agent: `writer_${i}`,
                    chapter_id: i,
                    status: 'completed',
                });
            }
            
            useChatStore.getState().handleWebSocketEvent('agent_completed', {
                agent: 'writer',
                status: 'completed',
            });
            
            const logs = useChatStore.getState().logs;
            expect(logs.filter(log => log.message.includes('writing completed')).length).toBe(5);
        });
    });
});

