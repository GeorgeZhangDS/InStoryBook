import { create } from 'zustand';

export type Message = {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: number;
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

interface ChatState {
    messages: Message[];
    agentSteps: AgentStep[];
    logs: LogEntry[];
    isGenerating: boolean;
    workflowBranch: WorkflowBranch;

    addMessage: (role: 'user' | 'assistant', content: string) => void;
    setAgentSteps: (steps: AgentStep[]) => void;
    updateAgentStep: (id: string, status: AgentStep['status'], details?: string) => void;
    addLog: (message: string, type?: LogEntry['type']) => void;
    setIsGenerating: (isGenerating: boolean) => void;
    setWorkflowBranch: (branch: WorkflowBranch) => void;
}

export const useChatStore = create<ChatState>((set) => ({
    messages: [],
    agentSteps: [
        { id: 'router', name: 'Router', status: 'pending' },
    ],
    logs: [],
    isGenerating: false,
    workflowBranch: 'router',

    addMessage: (role, content) => set((state) => ({
        messages: [...state.messages, {
            id: crypto.randomUUID(),
            role,
            content,
            timestamp: Date.now(),
        }]
    })),

    setAgentSteps: (steps) => set({ agentSteps: steps }),

    updateAgentStep: (id, status, details) => set((state) => ({
        agentSteps: state.agentSteps.map((step) =>
            step.id === id ? { ...step, status, details } : step
        )
    })),

    addLog: (message, type = 'info') => set((state) => ({
        logs: [...state.logs, {
            id: crypto.randomUUID(),
            timestamp: new Date().toLocaleTimeString(),
            message,
            type,
        }]
    })),

    setIsGenerating: (isGenerating) => set({ isGenerating }),
    setWorkflowBranch: (workflowBranch) => set({ workflowBranch }),
}));
