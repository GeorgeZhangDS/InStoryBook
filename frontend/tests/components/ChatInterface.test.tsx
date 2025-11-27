import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import ChatInterface from '@/components/ChatInterface';
import { useChatStore } from '@/stores/chatStore';

// Mock useWebSocket
vi.mock('@/hooks/useWebSocket', () => ({
    useWebSocket: vi.fn(() => ({
        sendMessage: vi.fn(() => true),
        isConnected: true,
        status: 'connected',
    })),
}));

describe('ChatInterface Component', () => {
    beforeEach(() => {
        useChatStore.getState().reset();
        useChatStore.getState().setWsConnected(true);
    });

    it('should render empty state when no messages', () => {
        render(<ChatInterface />);
        
        expect(screen.getByText('Start your story journey...')).toBeInTheDocument();
    });

    it('should render user messages', () => {
        useChatStore.getState().addMessage('user', 'Hello, I want a story');
        
        render(<ChatInterface />);
        
        expect(screen.getByText('Hello, I want a story')).toBeInTheDocument();
    });

    it('should render assistant messages', () => {
        useChatStore.getState().addMessage('assistant', 'I will create a story for you!');
        
        render(<ChatInterface />);
        
        expect(screen.getByText('I will create a story for you!')).toBeInTheDocument();
    });

    it('should send message on form submit', async () => {
        const { useWebSocket } = await import('@/hooks/useWebSocket');
        const mockSendMessage = vi.fn(() => true);
        
        vi.mocked(useWebSocket).mockReturnValue({
            sendMessage: mockSendMessage,
            isConnected: true,
            status: 'connected',
            connect: vi.fn(),
            disconnect: vi.fn(),
        });

        render(<ChatInterface />);
        
        const input = screen.getByPlaceholderText(/What happens next/i);
        const form = input.closest('form');
        
        fireEvent.change(input, { target: { value: 'Test message' } });
        fireEvent.submit(form!);
        
        await waitFor(() => {
            expect(mockSendMessage).toHaveBeenCalledWith('message', { theme: 'Test message' });
        });
    });

    it('should not send empty messages', () => {
        const { useWebSocket } = require('@/hooks/useWebSocket');
        const mockSendMessage = vi.fn();
        
        vi.mocked(useWebSocket).mockReturnValue({
            sendMessage: mockSendMessage,
            isConnected: true,
            status: 'connected',
            connect: vi.fn(),
            disconnect: vi.fn(),
        });

        render(<ChatInterface />);
        
        const input = screen.getByPlaceholderText(/What happens next/i);
        const form = input.closest('form');
        
        fireEvent.submit(form!);
        
        expect(mockSendMessage).not.toHaveBeenCalled();
    });

    it('should disable input when generating', () => {
        useChatStore.getState().setIsGenerating(true);
        
        render(<ChatInterface />);
        
        const input = screen.getByPlaceholderText(/What happens next/i) as HTMLInputElement;
        expect(input.disabled).toBe(true);
    });

    it('should disable input when not connected', () => {
        useChatStore.getState().setWsConnected(false);
        const { useWebSocket } = require('@/hooks/useWebSocket');
        
        vi.mocked(useWebSocket).mockReturnValue({
            sendMessage: vi.fn(),
            isConnected: false,
            status: 'disconnected',
            connect: vi.fn(),
            disconnect: vi.fn(),
        });

        render(<ChatInterface />);
        
        const input = screen.getByPlaceholderText(/Connecting to server/i) as HTMLInputElement;
        expect(input.disabled).toBe(true);
    });

    it('should display story chapters with images', () => {
        useChatStore.getState().addMessage('assistant', 'Story text');
        const messages = useChatStore.getState().messages;
        const lastMessage = messages[messages.length - 1];
        
        useChatStore.setState({
            messages: messages.map(msg => 
                msg.id === lastMessage.id 
                    ? {
                        ...msg,
                        storyChapters: [
                            {
                                chapter_id: 1,
                                title: 'Chapter 1',
                                text: 'Text 1',
                                image_url: 'https://example.com/image1.jpg',
                            },
                        ],
                    }
                    : msg
            ),
        });

        render(<ChatInterface />);
        
        const image = screen.getByAltText('Chapter 1');
        expect(image).toBeInTheDocument();
        expect(image).toHaveAttribute('src', 'https://example.com/image1.jpg');
    });

    it('should display loading state for chapters without images', () => {
        useChatStore.getState().addMessage('assistant', 'Story text');
        const messages = useChatStore.getState().messages;
        const lastMessage = messages[messages.length - 1];
        
        useChatStore.setState({
            messages: messages.map(msg => 
                msg.id === lastMessage.id 
                    ? {
                        ...msg,
                        storyChapters: [
                            {
                                chapter_id: 1,
                                title: 'Chapter 1',
                                text: 'Text 1',
                                // No image_url
                            },
                        ],
                    }
                    : msg
            ),
        });

        render(<ChatInterface />);
        
        expect(screen.getByText('Loading image...')).toBeInTheDocument();
    });
});

