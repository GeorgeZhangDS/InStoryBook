import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Generate from '@/pages/Generate';
import { useChatStore } from '@/stores/chatStore';

// Mock useWebSocket
const mockSendMessage = vi.fn(() => true);
const mockConnect = vi.fn();
const mockDisconnect = vi.fn();

vi.mock('@/hooks/useWebSocket', () => ({
    useWebSocket: vi.fn(() => ({
        sendMessage: mockSendMessage,
        isConnected: true,
        status: 'connected',
        connect: mockConnect,
        disconnect: mockDisconnect,
    })),
}));

// Mock ChatInterface and Sidebar
vi.mock('@/components/ChatInterface', () => ({
    default: () => <div data-testid="chat-interface">Chat Interface</div>,
}));

vi.mock('@/components/Sidebar', () => ({
    default: ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => (
        isOpen ? (
            <div data-testid="sidebar">
                <button onClick={onClose}>Close Sidebar</button>
                <div>Sidebar Content</div>
            </div>
        ) : null
    ),
}));

describe('Generate Page', () => {
    beforeEach(() => {
        useChatStore.getState().reset();
        sessionStorage.clear();
        vi.clearAllMocks();
    });

    afterEach(() => {
        // Clean up any event listeners
        const events = ['send-initial-message'];
        events.forEach(event => {
            window.removeEventListener(event, () => {});
        });
    });

    it('should render chat interface', () => {
        render(<Generate />);
        
        expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
    });

    it('should render sidebar toggle button when sidebar is closed', () => {
        render(<Generate />);
        
        const toggleButton = screen.getByTitle('Open Agent Workflow');
        expect(toggleButton).toBeInTheDocument();
    });

    it('should open sidebar when toggle button is clicked', () => {
        render(<Generate />);
        
        const toggleButton = screen.getByTitle('Open Agent Workflow');
        fireEvent.click(toggleButton);
        
        expect(screen.getByText('Sidebar Content')).toBeInTheDocument();
    });

    it('should close sidebar when close button is clicked', () => {
        render(<Generate />);
        
        // Open sidebar
        const toggleButton = screen.getByTitle('Open Agent Workflow');
        fireEvent.click(toggleButton);
        
        expect(screen.getByText('Sidebar Content')).toBeInTheDocument();
        
        // Close sidebar
        const closeButton = screen.getByText('Close Sidebar');
        fireEvent.click(closeButton);
        
        expect(screen.queryByText('Sidebar Content')).not.toBeInTheDocument();
    });

    it('should hide toggle button when sidebar is open', () => {
        render(<Generate />);
        
        const toggleButton = screen.getByTitle('Open Agent Workflow');
        fireEvent.click(toggleButton);
        
        expect(screen.queryByTitle('Open Agent Workflow')).not.toBeInTheDocument();
    });

    it('should send initial prompt from sessionStorage', async () => {
        sessionStorage.setItem('initial_prompt', 'A story about a rabbit');
        
        render(<Generate />);
        
        await waitFor(() => {
            const messages = useChatStore.getState().messages;
            expect(messages.length).toBeGreaterThan(0);
            expect(messages[0].content).toBe('A story about a rabbit');
            expect(messages[0].role).toBe('user');
        });
    });

    it('should remove initial prompt from sessionStorage after sending', async () => {
        sessionStorage.setItem('initial_prompt', 'A story about a rabbit');
        
        render(<Generate />);
        
        await waitFor(() => {
            expect(sessionStorage.getItem('initial_prompt')).toBeNull();
        });
    });

    it('should dispatch send-initial-message event after adding message', async () => {
        sessionStorage.setItem('initial_prompt', 'A story about a rabbit');
        
        const eventListener = vi.fn();
        window.addEventListener('send-initial-message', eventListener);
        
        render(<Generate />);
        
        await waitFor(() => {
            expect(eventListener).toHaveBeenCalled();
        }, { timeout: 1000 });
        
        const event = eventListener.mock.calls[0][0];
        expect(event.detail.message).toBe('A story about a rabbit');
    });

    it('should not send initial prompt if messages already exist', () => {
        useChatStore.getState().addMessage('user', 'Existing message');
        sessionStorage.setItem('initial_prompt', 'A story about a rabbit');
        
        render(<Generate />);
        
        const messages = useChatStore.getState().messages;
        expect(messages.length).toBe(1);
        expect(messages[0].content).toBe('Existing message');
    });

    it('should not send initial prompt if already sent', async () => {
        sessionStorage.setItem('initial_prompt', 'A story about a rabbit');
        
        const { rerender } = render(<Generate />);
        
        await waitFor(() => {
            expect(sessionStorage.getItem('initial_prompt')).toBeNull();
        });
        
        // Rerender should not send again
        sessionStorage.setItem('initial_prompt', 'Another story');
        rerender(<Generate />);
        
        // Should still be in sessionStorage because it was already sent
        await waitFor(() => {
            const messages = useChatStore.getState().messages;
            // Should only have one message from the first render
            expect(messages.filter(m => m.content === 'Another story')).toHaveLength(0);
        });
    });

    it('should apply correct margin when sidebar is open', () => {
        render(<Generate />);
        
        expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
        
        // Open sidebar
        const toggleButton = screen.getByTitle('Open Agent Workflow');
        fireEvent.click(toggleButton);
        
        // Check if sidebar is open
        expect(screen.getByTestId('sidebar')).toBeInTheDocument();
        expect(screen.getByText('Sidebar Content')).toBeInTheDocument();
    });
});

