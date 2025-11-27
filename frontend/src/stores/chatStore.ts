/* =========================
   Zustand Global Store
========================= */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/* =========================
   Types
========================= */

export type Message = {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: number;
    storyChapters?: Chapter[];
    needsTypewriter?: boolean; // Flag to indicate if message should use typewriter effect
};

export type AgentStep = {
    id: string;
    name: string;
    status: 'pending' | 'active' | 'completed' | 'failed';
    details?: string;
};

export type LogEntry = {
    id: string;
    timestamp: string;
    message: string;
    type: 'info' | 'success' | 'warning' | 'error';
};

export type WorkflowBranch = 'router' | 'story-graph' | 'chat';

export type Chapter = {
    chapter_id: number;
    title: string;
    text: string;
    image_url?: string;
    image_prompt?: string;
};

export type StoryOutline = {
    style?: string;
    characters?: string[];
    setting?: string;
    plot_summary?: string;
    language?: string;
};



/* =========================
   Store State Interface
========================= */

interface ChatState {
    sessionId: string | null;
    messages: Message[];
    agentSteps: AgentStep[];
    logs: LogEntry[];
    isGenerating: boolean;
    workflowBranch: WorkflowBranch;
    chapters: Chapter[];
    storyOutline: StoryOutline | null;
    wsConnected: boolean;

    setSessionId: (sessionId: string | null) => void;
    getOrCreateSessionId: () => string;
    addMessage: (role: 'user' | 'assistant', content: string) => void;
    setAgentSteps: (steps: AgentStep[]) => void;
    updateAgentStep: (id: string, status: AgentStep['status'], details?: string) => void;
    addLog: (message: string, type?: LogEntry['type'], timestamp?: string) => void;
    setIsGenerating: (isGenerating: boolean) => void;
    setWorkflowBranch: (branch: WorkflowBranch) => void;
    setWsConnected: (connected: boolean) => void;
    setChapters: (chapters: Chapter[]) => void;
    updateChapters: (chapters: Chapter[]) => void;
    setStoryOutline: (outline: StoryOutline | null) => void;
    handleWebSocketEvent: (eventType: string, data: Record<string, any>, timestamp?: number) => void;
    reset: () => void;
}



/* =========================
   Store Definition
========================= */

const generateSessionId = (): string => {
    return crypto.randomUUID();
};

export const useChatStore = create<ChatState>()(
    persist(
        (set, get) => ({
    /* =========================
       Initial State
    ========================= */

            sessionId: null,
    messages: [],
    agentSteps: [
        { id: 'router', name: 'Router', status: 'pending' },
    ],
    logs: [],
    isGenerating: false,
    workflowBranch: 'router',
            chapters: [],
            storyOutline: null,
            wsConnected: false,

            /* =========================
               Session Management
            ========================= */

            setSessionId: (sessionId) => set({ sessionId }),

            getOrCreateSessionId: () => {
                const state = get();
                if (!state.sessionId) {
                    const newSessionId = generateSessionId();
                    set({ sessionId: newSessionId });
                    return newSessionId;
                }
                return state.sessionId;
            },



    /* =========================
       Actions - Message
    ========================= */

    addMessage: (role, content) => set((state) => ({
        messages: [
            ...state.messages,
            {
                id: crypto.randomUUID(),
                role,
                content,
                timestamp: Date.now(),
            }
        ]
    })),



    /* =========================
       Actions - Agent Workflow
    ========================= */

    setAgentSteps: (steps) => set({ agentSteps: steps }),

    updateAgentStep: (id, status, details) => set((state) => ({
        agentSteps: state.agentSteps.map((step) =>
            step.id === id ? { ...step, status, details } : step
        )
    })),



    /* =========================
       Actions - Logs
    ========================= */

    addLog: (message, type = 'info', timestamp?: string) => set((state) => ({
        logs: [
            ...state.logs,
            {
                id: crypto.randomUUID(),
                timestamp: timestamp || new Date().toLocaleTimeString(),
                message,
                type,
            }
        ]
    })),

    /* =========================
       Actions - Global Flags
    ========================= */

    setIsGenerating: (isGenerating) => set({ isGenerating }),

    setWorkflowBranch: (workflowBranch) => set({ workflowBranch }),

            setWsConnected: (connected) => set({ wsConnected: connected }),

            /* =========================
               Actions - Story Data
            ========================= */

            setChapters: (chapters) => set({ chapters }),

            updateChapters: (newChapters) => set((state) => {
                const updated = [...state.chapters];
                newChapters.forEach((chapter: any) => {
                    const normalizedChapter: Chapter = {
                        chapter_id: chapter.chapter_id,
                        title: chapter.title || state.chapters.find(c => c.chapter_id === chapter.chapter_id)?.title || `Chapter ${chapter.chapter_id}`,
                        text: chapter.text || chapter.content || state.chapters.find(c => c.chapter_id === chapter.chapter_id)?.text || '',
                        image_url: chapter.image_url || chapter.image || state.chapters.find(c => c.chapter_id === chapter.chapter_id)?.image_url || undefined,
                        image_prompt: chapter.image_prompt || state.chapters.find(c => c.chapter_id === chapter.chapter_id)?.image_prompt || undefined,
                    };
                    
                    const index = updated.findIndex((c) => c.chapter_id === normalizedChapter.chapter_id);
                    if (index >= 0) {
                        updated[index] = { ...updated[index], ...normalizedChapter };
                    } else {
                        updated.push(normalizedChapter);
                    }
                });
                updated.sort((a, b) => a.chapter_id - b.chapter_id);
                console.log('updateChapters result:', updated.map(ch => ({ id: ch.chapter_id, title: ch.title, hasImage: !!ch.image_url, imageUrl: ch.image_url })));
                return { chapters: updated };
            }),

            setStoryOutline: (outline) => set({ storyOutline: outline }),

            /* =========================
               Actions - WebSocket Events
            ========================= */

            handleWebSocketEvent: (eventType, data, timestamp?: number) => {
                const logTimestamp = timestamp ? new Date(timestamp * 1000).toLocaleTimeString() : undefined;
                switch (eventType) {
                    case 'session_ready':
                        set({ wsConnected: true });
                        get().addLog('WebSocket connected', 'success', logTimestamp);
                        break;

                    case 'agent_started':
                        const agentName = data.agent || 'unknown';
                        const stepName = agentName === 'planner' ? 'planning' : 
                                       agentName === 'chat' ? 'chat' : 
                                       agentName === 'writer' ? 'writing' :
                                       agentName;
                        get().addLog(`${agentName} started`, 'info', logTimestamp);
                        if (agentName === 'planner') {
                            get().setWorkflowBranch('story-graph');
                            get().setAgentSteps([
                                { id: 'router', name: 'Router', status: 'completed', details: 'Route: Story Graph' },
                                { id: 'planning', name: 'Planning Story', status: 'active', details: data.status || 'running' },
                                { id: 'writing', name: 'Writing Content', status: 'pending' },
                                { id: 'illustrating', name: 'Generating Illustrations', status: 'pending' },
                            ]);
                        } else if (agentName === 'writer') {
                            get().updateAgentStep('planning', 'completed');
                            get().updateAgentStep('writing', 'active');
                        } else if (agentName === 'illustrator') {
                            get().updateAgentStep('illustrating', 'active');
                        } else if (agentName === 'chat') {
                            get().setWorkflowBranch('chat');
                            get().setAgentSteps([
                                { id: 'router', name: 'Router', status: 'completed', details: 'Route: Chat' },
                                { id: 'chat', name: 'Chat', status: 'active', details: data.status || 'running' },
                            ]);
                        } else {
                            get().updateAgentStep(stepName, 'active', data.status || 'running');
                        }
                        break;
                    
                    case 'agent_completed':
                        const completedAgentName = data.agent || 'unknown';
                        if (completedAgentName === 'planner') {
                            get().updateAgentStep('planning', 'completed');
                            get().addLog('Planning completed', 'success', logTimestamp);
                        } else if (completedAgentName === 'writer') {
                            get().updateAgentStep('writing', 'completed');
                            get().addLog('All chapters writing completed', 'success', logTimestamp);
                        } else if (completedAgentName.startsWith('writer_')) {
                            const chapterId = data.chapter_id;
                            get().addLog(`Chapter ${chapterId} writing completed`, 'success', logTimestamp);
                        } else if (completedAgentName.startsWith('illustrator_')) {
                            const chapterId = data.chapter_id;
                            get().addLog(`Chapter ${chapterId} illustration completed`, 'success', logTimestamp);
                        } else if (completedAgentName === 'chat') {
                            get().updateAgentStep('chat', 'completed');
                        } else if (completedAgentName === 'illustrator') {
                            get().updateAgentStep('illustrating', 'completed');
                            get().addLog('Illustrating completed', 'success', logTimestamp);
                        }
                        break;

                    case 'chat_response':
                        get().addMessage('assistant', data.response || '');
                        const chatMessages = get().messages;
                        const lastChatMessage = chatMessages[chatMessages.length - 1];
                        if (lastChatMessage) {
                            set((state) => ({
                                messages: state.messages.map(msg => 
                                    msg.id === lastChatMessage.id 
                                        ? { ...msg, needsTypewriter: true }
                                        : msg
                                )
                            }));
                        }
                        get().updateAgentStep('chat', 'completed');
                        get().setIsGenerating(false);
                        break;

                    case 'finalizer_text':
                        if (data.chapters && Array.isArray(data.chapters)) {
                            get().updateChapters(data.chapters);
                            // Writing step should already be completed when all writers finish
                            // But ensure it's completed here as well
                            get().updateAgentStep('writing', 'completed');
                            get().addLog('Story text finalized', 'success', logTimestamp);
                            
                            const storyText = data.chapters
                                .map((ch: any) => `**${ch.title || `Chapter ${ch.chapter_id}`}**\n\n${ch.content || ch.text || ''}`)
                                .join('\n\n---\n\n');
                            
                            const normalizedChapters = data.chapters.map((ch: any) => ({
                                chapter_id: ch.chapter_id,
                                title: ch.title || `Chapter ${ch.chapter_id}`,
                                text: ch.text || ch.content || '',
                                image_url: undefined,
                                image_prompt: ch.image_prompt,
                            }));
                            
                            get().addMessage('assistant', storyText);
                            const messages = get().messages;
                            const lastMessage = messages[messages.length - 1];
                            if (lastMessage) {
                                set((state) => ({
                                    messages: state.messages.map(msg => 
                                        msg.id === lastMessage.id 
                                            ? { ...msg, storyChapters: normalizedChapters, needsTypewriter: true }
                                            : msg
                                    )
                                }));
                            }
                        }
                        break;

                    case 'finalizer_image':
                        if (data.chapters && Array.isArray(data.chapters)) {
                            console.log('finalizer_image received:', data.chapters);
                            get().updateChapters(data.chapters);
                            const updatedChapters = get().chapters;
                            console.log('Updated chapters:', updatedChapters.map(ch => ({ id: ch.chapter_id, hasImage: !!ch.image_url })));
                            
                            const messages = get().messages;
                            const lastStoryMessage = [...messages].reverse().find(msg => msg.role === 'assistant' && msg.storyChapters);
                            if (lastStoryMessage && lastStoryMessage.storyChapters) {
                                set((state) => ({
                                    messages: state.messages.map(msg => 
                                        msg.id === lastStoryMessage.id && msg.storyChapters
                                            ? {
                                                ...msg,
                                                storyChapters: msg.storyChapters.map(ch => {
                                                    const updatedChapter = updatedChapters.find(uc => uc.chapter_id === ch.chapter_id);
                                                    return updatedChapter ? { ...ch, image_url: updatedChapter.image_url } : ch;
                                                })
                                            }
                                            : msg
                                    )
                                }));
                            }
                            
                            get().updateAgentStep('illustrating', 'completed');
                            get().addLog('Story images finalized', 'success', logTimestamp);
                        }
                        break;

                    case 'pipeline_completed':
                        get().setIsGenerating(false);
                        const workflowBranch = get().workflowBranch;
                        if (workflowBranch === 'story-graph') {
                            get().addLog('Story generation completed', 'success', logTimestamp);
                            get().updateAgentStep('planning', 'completed');
                            get().updateAgentStep('writing', 'completed');
                            get().updateAgentStep('illustrating', 'completed');
                        } else if (workflowBranch === 'chat') {
                            get().addLog('Chat completed', 'success', logTimestamp);
                            get().updateAgentStep('chat', 'completed');
                        }
                        break;

                    case 'error':
                        get().addLog(`Error: ${data.error || 'Unknown error'}`, 'error');
                        get().setIsGenerating(false);
                        if (data.agent) {
                            get().updateAgentStep(data.agent, 'failed', data.error);
                        }
                        break;

                    default:
                        console.warn('Unknown WebSocket event type:', eventType);
                }
            },

            /* =========================
               Actions - Reset
            ========================= */

            reset: () => set({
                messages: [],
                agentSteps: [{ id: 'router', name: 'Router', status: 'pending' }],
                logs: [],
                isGenerating: false,
                workflowBranch: 'router',
                chapters: [],
                storyOutline: null,
            }),
        }),
        {
            name: 'chat-store',
            storage: {
                getItem: (name: string) => {
                    const str = sessionStorage.getItem(name);
                    return str ? JSON.parse(str) : null;
                },
                setItem: (name: string, value: any) => {
                    sessionStorage.setItem(name, JSON.stringify(value));
                },
                removeItem: (name: string) => {
                    sessionStorage.removeItem(name);
                },
            },
            partialize: (state) => ({
                sessionId: state.sessionId,
                messages: state.messages,
                chapters: state.chapters,
                storyOutline: state.storyOutline,
                workflowBranch: state.workflowBranch,
                agentSteps: state.agentSteps,
            }) as Partial<ChatState>,
        }
    )
);