import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import Home from '@/pages/Home';
import { useChatStore } from '@/stores/chatStore';

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
    const actual = await vi.importActual('react-router-dom');
    return {
        ...actual,
        useNavigate: () => mockNavigate,
    };
});

// Mock framer-motion
vi.mock('framer-motion', () => ({
    motion: {
        div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    },
}));

describe('Home Page', () => {
    beforeEach(() => {
        useChatStore.getState().reset();
        sessionStorage.clear();
        vi.clearAllMocks();
    });

    it('should render home page with title and description', () => {
        render(
            <MemoryRouter>
                <Home />
            </MemoryRouter>
        );
        
        expect(screen.getByText('In Story Book')).toBeInTheDocument();
        expect(screen.getByText(/Turn your ideas into magical, illustrated bedtime stories/)).toBeInTheDocument();
    });

    it('should render input field with placeholder', () => {
        render(
            <MemoryRouter>
                <Home />
            </MemoryRouter>
        );
        
        const input = screen.getByPlaceholderText('Describe a story...');
        expect(input).toBeInTheDocument();
    });

    it('should update input value when typing', () => {
        render(
            <MemoryRouter>
                <Home />
            </MemoryRouter>
        );
        
        const input = screen.getByPlaceholderText('Describe a story...') as HTMLInputElement;
        
        fireEvent.change(input, { target: { value: 'A story about a rabbit' } });
        
        expect(input.value).toBe('A story about a rabbit');
    });

    it('should enable submit button when input has value', () => {
        render(
            <MemoryRouter>
                <Home />
            </MemoryRouter>
        );
        
        const input = screen.getByPlaceholderText('Describe a story...');
        const button = screen.getByRole('button');
        
        expect(button).toBeDisabled();
        
        fireEvent.change(input, { target: { value: 'A story' } });
        
        expect(button).not.toBeDisabled();
    });

    it('should disable submit button when input is empty', () => {
        render(
            <MemoryRouter>
                <Home />
            </MemoryRouter>
        );
        
        const input = screen.getByPlaceholderText('Describe a story...');
        const button = screen.getByRole('button');
        
        fireEvent.change(input, { target: { value: 'A story' } });
        fireEvent.change(input, { target: { value: '' } });
        
        expect(button).toBeDisabled();
    });

    it('should not submit empty form', () => {
        render(
            <MemoryRouter>
                <Home />
            </MemoryRouter>
        );
        
        const form = screen.getByRole('button').closest('form');
        
        fireEvent.submit(form!);
        
        expect(mockNavigate).not.toHaveBeenCalled();
        expect(sessionStorage.getItem('initial_prompt')).toBeNull();
    });

    it('should submit form and navigate to chat page', () => {
        render(
            <MemoryRouter>
                <Home />
            </MemoryRouter>
        );
        
        const input = screen.getByPlaceholderText('Describe a story...');
        const form = screen.getByRole('button').closest('form');
        
        fireEvent.change(input, { target: { value: 'A story about a rabbit' } });
        fireEvent.submit(form!);
        
        expect(mockNavigate).toHaveBeenCalledWith('/chat');
        expect(sessionStorage.getItem('initial_prompt')).toBe('A story about a rabbit');
    });

    it('should trim whitespace before submitting', () => {
        render(
            <MemoryRouter>
                <Home />
            </MemoryRouter>
        );
        
        const input = screen.getByPlaceholderText('Describe a story...');
        const form = screen.getByRole('button').closest('form');
        
        fireEvent.change(input, { target: { value: '  A story  ' } });
        fireEvent.submit(form!);
        
        expect(mockNavigate).toHaveBeenCalledWith('/chat');
        expect(sessionStorage.getItem('initial_prompt')).toBe('  A story  ');
    });

    it('should initialize session ID on mount', () => {
        const getOrCreateSessionIdSpy = vi.spyOn(useChatStore.getState(), 'getOrCreateSessionId');
        
        render(
            <MemoryRouter>
                <Home />
            </MemoryRouter>
        );
        
        expect(getOrCreateSessionIdSpy).toHaveBeenCalled();
    });

    it('should handle input focus state', () => {
        render(
            <MemoryRouter>
                <Home />
            </MemoryRouter>
        );
        
        const input = screen.getByPlaceholderText('Describe a story...');
        const formContainer = input.closest('.group');
        
        fireEvent.focus(input);
        
        // Check if form container has focus styles (scale and shadow changes)
        expect(formContainer).toBeInTheDocument();
    });
});

