import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore, Message, Chapter, AgentStep } from '@/stores/chatStore';

describe('ChatStore', () => {
    beforeEach(() => {
        // Reset store before each test
        useChatStore.getState().reset();
    });

    describe('Session Management', () => {
        it('should generate and store sessionId', () => {
            const sessionId = useChatStore.getState().getOrCreateSessionId();
            
            expect(sessionId).toBeTruthy();
            expect(typeof sessionId).toBe('string');
            expect(sessionId.length).toBeGreaterThan(0);
        });

        it('should return same sessionId on subsequent calls', () => {
            const sessionId1 = useChatStore.getState().getOrCreateSessionId();
            const sessionId2 = useChatStore.getState().getOrCreateSessionId();
            
            expect(sessionId1).toBe(sessionId2);
        });

        it('should set sessionId manually', () => {
            const testSessionId = 'test-session-123';
            useChatStore.getState().setSessionId(testSessionId);
            
            expect(useChatStore.getState().sessionId).toBe(testSessionId);
        });
    });

    describe('Message Management', () => {
        it('should add user message', () => {
            const content = 'Hello, I want a story about a rabbit';
            useChatStore.getState().addMessage('user', content);
            
            const messages = useChatStore.getState().messages;
            expect(messages.length).toBe(1);
            expect(messages[0].role).toBe('user');
            expect(messages[0].content).toBe(content);
            expect(messages[0].timestamp).toBeGreaterThan(0);
        });

        it('should add assistant message', () => {
            const content = 'I will create a story for you!';
            useChatStore.getState().addMessage('assistant', content);
            
            const messages = useChatStore.getState().messages;
            expect(messages.length).toBe(1);
            expect(messages[0].role).toBe('assistant');
            expect(messages[0].content).toBe(content);
        });

        it('should add multiple messages in order', () => {
            useChatStore.getState().addMessage('user', 'First message');
            useChatStore.getState().addMessage('assistant', 'Second message');
            useChatStore.getState().addMessage('user', 'Third message');
            
            const messages = useChatStore.getState().messages;
            expect(messages.length).toBe(3);
            expect(messages[0].content).toBe('First message');
            expect(messages[1].content).toBe('Second message');
            expect(messages[2].content).toBe('Third message');
        });

        it('should generate unique message IDs', () => {
            useChatStore.getState().addMessage('user', 'Message 1');
            useChatStore.getState().addMessage('user', 'Message 2');
            
            const messages = useChatStore.getState().messages;
            expect(messages[0].id).not.toBe(messages[1].id);
        });
    });

    describe('Agent Steps Management', () => {
        it('should set agent steps', () => {
            const steps: AgentStep[] = [
                { id: 'planning', name: 'Planning', status: 'active' },
                { id: 'writing', name: 'Writing', status: 'pending' },
            ];
            
            useChatStore.getState().setAgentSteps(steps);
            
            expect(useChatStore.getState().agentSteps).toEqual(steps);
        });

        it('should update agent step status', () => {
            const steps: AgentStep[] = [
                { id: 'planning', name: 'Planning', status: 'pending' },
            ];
            
            useChatStore.getState().setAgentSteps(steps);
            useChatStore.getState().updateAgentStep('planning', 'active', 'Running...');
            
            const updatedSteps = useChatStore.getState().agentSteps;
            expect(updatedSteps[0].status).toBe('active');
            expect(updatedSteps[0].details).toBe('Running...');
        });

        it('should not update non-existent step', () => {
            useChatStore.getState().setAgentSteps([
                { id: 'planning', name: 'Planning', status: 'pending' },
            ]);
            
            useChatStore.getState().updateAgentStep('nonexistent', 'active');
            
            const steps = useChatStore.getState().agentSteps;
            expect(steps.find(s => s.id === 'nonexistent')).toBeUndefined();
        });
    });

    describe('Log Management', () => {
        it('should add log entry', () => {
            useChatStore.getState().addLog('Test log message', 'info');
            
            const logs = useChatStore.getState().logs;
            expect(logs.length).toBe(1);
            expect(logs[0].message).toBe('Test log message');
            expect(logs[0].type).toBe('info');
            expect(logs[0].timestamp).toBeTruthy();
        });

        it('should add different log types', () => {
            useChatStore.getState().addLog('Info message', 'info');
            useChatStore.getState().addLog('Success message', 'success');
            useChatStore.getState().addLog('Warning message', 'warning');
            useChatStore.getState().addLog('Error message', 'error');
            
            const logs = useChatStore.getState().logs;
            expect(logs.length).toBe(4);
            expect(logs[0].type).toBe('info');
            expect(logs[1].type).toBe('success');
            expect(logs[2].type).toBe('warning');
            expect(logs[3].type).toBe('error');
        });

        it('should add log with custom timestamp', () => {
            const customTimestamp = '10:30:45 AM';
            useChatStore.getState().addLog('Test message', 'info', customTimestamp);
            
            const logs = useChatStore.getState().logs;
            expect(logs[0].timestamp).toBe(customTimestamp);
        });
    });

    describe('WebSocket Event Handling', () => {
        it('should handle session_ready event', () => {
            useChatStore.getState().handleWebSocketEvent('session_ready', {});
            
            expect(useChatStore.getState().wsConnected).toBe(true);
            const logs = useChatStore.getState().logs;
            expect(logs.some(log => log.message.includes('WebSocket connected'))).toBe(true);
        });

        it('should handle agent_started event for planner', () => {
            useChatStore.getState().handleWebSocketEvent('agent_started', {
                agent: 'planner',
                status: 'running',
            });
            
            const steps = useChatStore.getState().agentSteps;
            expect(steps.find(s => s.id === 'planning')?.status).toBe('active');
            expect(useChatStore.getState().workflowBranch).toBe('story-graph');
        });

        it('should handle agent_started event for chat', () => {
            useChatStore.getState().handleWebSocketEvent('agent_started', {
                agent: 'chat',
                status: 'running',
            });
            
            const steps = useChatStore.getState().agentSteps;
            expect(steps.find(s => s.id === 'chat')?.status).toBe('active');
            expect(useChatStore.getState().workflowBranch).toBe('chat');
        });

        it('should handle chat_response event', () => {
            const responseText = 'Hello! How can I help you today?';
            useChatStore.getState().handleWebSocketEvent('chat_response', {
                response: responseText,
            });
            
            const messages = useChatStore.getState().messages;
            expect(messages.length).toBe(1);
            expect(messages[0].role).toBe('assistant');
            expect(messages[0].content).toBe(responseText);
            expect(messages[0].needsTypewriter).toBe(true);
            expect(useChatStore.getState().isGenerating).toBe(false);
        });

        it('should handle finalizer_text event', () => {
            const chapters = [
                {
                    chapter_id: 1,
                    title: 'Chapter 1',
                    content: 'Once upon a time...',
                    text: 'Once upon a time...',
                },
                {
                    chapter_id: 2,
                    title: 'Chapter 2',
                    content: 'The adventure continues...',
                    text: 'The adventure continues...',
                },
            ];
            
            useChatStore.getState().handleWebSocketEvent('finalizer_text', {
                chapters,
            });
            
            const messages = useChatStore.getState().messages;
            expect(messages.length).toBe(1);
            expect(messages[0].role).toBe('assistant');
            expect(messages[0].storyChapters).toBeDefined();
            expect(messages[0].storyChapters?.length).toBe(2);
            expect(messages[0].storyChapters?.[0].chapter_id).toBe(1);
            expect(messages[0].storyChapters?.[1].chapter_id).toBe(2);
        });

        it('should handle finalizer_image event and update chapters', () => {
            // First add text message with chapters
            const textChapters = [
                {
                    chapter_id: 1,
                    title: 'Chapter 1',
                    text: 'Story text',
                },
                {
                    chapter_id: 2,
                    title: 'Chapter 2',
                    text: 'More story text',
                },
            ];
            
            useChatStore.getState().handleWebSocketEvent('finalizer_text', {
                chapters: textChapters,
            });
            
            // Then add images
            const imageChapters = [
                {
                    chapter_id: 1,
                    image: 'https://example.com/image1.jpg',
                },
                {
                    chapter_id: 2,
                    image: 'https://example.com/image2.jpg',
                },
            ];
            
            useChatStore.getState().handleWebSocketEvent('finalizer_image', {
                chapters: imageChapters,
            });
            
            const messages = useChatStore.getState().messages;
            const storyMessage = messages.find(m => m.storyChapters);
            
            expect(storyMessage).toBeDefined();
            expect(storyMessage?.storyChapters?.[0].image_url).toBe('https://example.com/image1.jpg');
            expect(storyMessage?.storyChapters?.[1].image_url).toBe('https://example.com/image2.jpg');
        });

        it('should handle agent_completed event for planner', () => {
            useChatStore.getState().setAgentSteps([
                { id: 'planning', name: 'Planning', status: 'active' },
            ]);
            
            useChatStore.getState().handleWebSocketEvent('agent_completed', {
                agent: 'planner',
                status: 'completed',
            });
            
            const steps = useChatStore.getState().agentSteps;
            expect(steps.find(s => s.id === 'planning')?.status).toBe('completed');
        });

        it('should handle agent_completed event for writer', () => {
            useChatStore.getState().setAgentSteps([
                { id: 'writing', name: 'Writing', status: 'active' },
            ]);
            
            useChatStore.getState().handleWebSocketEvent('agent_completed', {
                agent: 'writer',
                status: 'completed',
            });
            
            const steps = useChatStore.getState().agentSteps;
            expect(steps.find(s => s.id === 'writing')?.status).toBe('completed');
        });

        it('should handle agent_completed event for individual writer chapters', () => {
            useChatStore.getState().handleWebSocketEvent('agent_completed', {
                agent: 'writer_1',
                chapter_id: 1,
                status: 'completed',
            });
            
            const logs = useChatStore.getState().logs;
            expect(logs.some(log => log.message.includes('Chapter 1 writing completed'))).toBe(true);
        });

        it('should handle agent_completed event for illustrator', () => {
            useChatStore.getState().setAgentSteps([
                { id: 'illustrating', name: 'Illustrating', status: 'active' },
            ]);
            
            useChatStore.getState().handleWebSocketEvent('agent_completed', {
                agent: 'illustrator',
                status: 'completed',
            });
            
            const steps = useChatStore.getState().agentSteps;
            expect(steps.find(s => s.id === 'illustrating')?.status).toBe('completed');
        });

        it('should handle pipeline_completed event for story-graph', () => {
            useChatStore.getState().setWorkflowBranch('story-graph');
            useChatStore.getState().setIsGenerating(true);
            
            useChatStore.getState().handleWebSocketEvent('pipeline_completed', {
                status: 'completed',
            });
            
            expect(useChatStore.getState().isGenerating).toBe(false);
            const logs = useChatStore.getState().logs;
            expect(logs.some(log => log.message.includes('Story generation completed'))).toBe(true);
        });

        it('should handle pipeline_completed event for chat', () => {
            useChatStore.getState().setWorkflowBranch('chat');
            useChatStore.getState().setIsGenerating(true);
            
            useChatStore.getState().handleWebSocketEvent('pipeline_completed', {
                status: 'completed',
            });
            
            expect(useChatStore.getState().isGenerating).toBe(false);
            const logs = useChatStore.getState().logs;
            expect(logs.some(log => log.message.includes('Chat completed'))).toBe(true);
        });

        it('should handle error event', () => {
            useChatStore.getState().handleWebSocketEvent('error', {
                agent: 'story_generation',
                error: 'Test error message',
            });
            
            const logs = useChatStore.getState().logs;
            const errorLog = logs.find(log => log.type === 'error');
            expect(errorLog).toBeDefined();
            expect(errorLog?.message).toContain('Test error message');
            expect(useChatStore.getState().isGenerating).toBe(false);
        });
    });

    describe('Chapter Management', () => {
        it('should set chapters', () => {
            const chapters: Chapter[] = [
                {
                    chapter_id: 1,
                    title: 'Chapter 1',
                    text: 'Content 1',
                    image_url: 'url1.jpg',
                },
                {
                    chapter_id: 2,
                    title: 'Chapter 2',
                    text: 'Content 2',
                },
            ];
            
            useChatStore.getState().setChapters(chapters);
            
            expect(useChatStore.getState().chapters).toEqual(chapters);
        });

        it('should update chapters', () => {
            const initialChapters: Chapter[] = [
                {
                    chapter_id: 1,
                    title: 'Chapter 1',
                    text: 'Content 1',
                },
            ];
            
            useChatStore.getState().setChapters(initialChapters);
            
            const updatedChapters = [
                {
                    chapter_id: 1,
                    title: 'Chapter 1',
                    text: 'Content 1',
                    image_url: 'new-image.jpg',
                },
                {
                    chapter_id: 2,
                    title: 'Chapter 2',
                    text: 'Content 2',
                },
            ];
            
            useChatStore.getState().updateChapters(updatedChapters);
            
            const chapters = useChatStore.getState().chapters;
            expect(chapters.length).toBe(2);
            expect(chapters[0].image_url).toBe('new-image.jpg');
        });

        it('should merge chapter updates correctly', () => {
            useChatStore.getState().setChapters([
                {
                    chapter_id: 1,
                    title: 'Chapter 1',
                    text: 'Original text',
                },
            ]);
            
            useChatStore.getState().updateChapters([
                {
                    chapter_id: 1,
                    title: 'Chapter 1',
                    text: 'Updated text',
                    image_url: 'image.jpg',
                },
            ]);
            
            const chapters = useChatStore.getState().chapters;
            expect(chapters[0].text).toBe('Updated text');
            expect(chapters[0].image_url).toBe('image.jpg');
        });
    });

    describe('Story Outline Management', () => {
        it('should set story outline', () => {
            const outline = {
                style: 'adventure',
                characters: ['Rabbit', 'Fox'],
                setting: 'Forest',
                plot_summary: 'A brave rabbit goes on an adventure',
            };
            
            useChatStore.getState().setStoryOutline(outline);
            
            expect(useChatStore.getState().storyOutline).toEqual(outline);
        });

        it('should clear story outline when set to null', () => {
            useChatStore.getState().setStoryOutline({
                style: 'adventure',
                characters: ['Rabbit'],
            });
            
            useChatStore.getState().setStoryOutline(null);
            
            expect(useChatStore.getState().storyOutline).toBeNull();
        });
    });

    describe('State Reset', () => {
        it('should reset all state', () => {
            // Set up some state
            useChatStore.getState().addMessage('user', 'Test');
            useChatStore.getState().setAgentSteps([
                { id: 'planning', name: 'Planning', status: 'active' },
            ]);
            useChatStore.getState().setIsGenerating(true);
            useChatStore.getState().setWorkflowBranch('story-graph');
            
            useChatStore.getState().reset();
            
            expect(useChatStore.getState().messages.length).toBe(0);
            expect(useChatStore.getState().agentSteps.length).toBe(0);
            expect(useChatStore.getState().isGenerating).toBe(false);
            expect(useChatStore.getState().workflowBranch).toBe('router');
            expect(useChatStore.getState().chapters.length).toBe(0);
            expect(useChatStore.getState().storyOutline).toBeNull();
        });
    });

    describe('WebSocket Connection State', () => {
        it('should set WebSocket connection state', () => {
            expect(useChatStore.getState().wsConnected).toBe(false);
            
            useChatStore.getState().setWsConnected(true);
            expect(useChatStore.getState().wsConnected).toBe(true);
            
            useChatStore.getState().setWsConnected(false);
            expect(useChatStore.getState().wsConnected).toBe(false);
        });
    });
});

