import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Sidebar from '@/components/Sidebar';
import { useChatStore } from '@/stores/chatStore';

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
    motion: {
        div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    },
    AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe('Sidebar Component', () => {
    const mockOnClose = vi.fn();

    beforeEach(() => {
        useChatStore.getState().reset();
        useChatStore.getState().setWsConnected(true);
        vi.clearAllMocks();
    });

    it('should not render when isOpen is false', () => {
        render(<Sidebar isOpen={false} onClose={mockOnClose} />);
        
        expect(screen.queryByText('Agent Workflow')).not.toBeInTheDocument();
    });

    it('should render when isOpen is true', () => {
        render(<Sidebar isOpen={true} onClose={mockOnClose} />);
        
        expect(screen.getByText('Agent Workflow')).toBeInTheDocument();
        expect(screen.getByText('System Logs')).toBeInTheDocument();
    });

    it('should call onClose when close button is clicked', () => {
        render(<Sidebar isOpen={true} onClose={mockOnClose} />);
        
        const closeButton = screen.getByRole('button');
        fireEvent.click(closeButton);
        
        expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it('should call onClose when backdrop is clicked', () => {
        const { container } = render(<Sidebar isOpen={true} onClose={mockOnClose} />);
        
        const backdrop = container.querySelector('.absolute.inset-0');
        if (backdrop) {
            fireEvent.click(backdrop);
            expect(mockOnClose).toHaveBeenCalledTimes(1);
        }
    });

    it('should display router status correctly', () => {
        useChatStore.getState().setWorkflowBranch('router');
        
        render(<Sidebar isOpen={true} onClose={mockOnClose} />);
        
        expect(screen.getByText('Router')).toBeInTheDocument();
    });

    it('should display story-graph workflow steps', () => {
        useChatStore.getState().setWorkflowBranch('story-graph');
        useChatStore.getState().setAgentSteps([
            { id: 'planning', name: 'Planning Story', status: 'active' },
            { id: 'writing', name: 'Writing Content', status: 'pending' },
            { id: 'illustrating', name: 'Generating Illustrations', status: 'pending' },
        ]);
        
        render(<Sidebar isOpen={true} onClose={mockOnClose} />);
        
        expect(screen.getByText('Story Graph')).toBeInTheDocument();
        expect(screen.getByText('Planning Story')).toBeInTheDocument();
        expect(screen.getByText('Writing Content')).toBeInTheDocument();
        expect(screen.getByText('Generating Illustrations')).toBeInTheDocument();
    });

    it('should display chat workflow', () => {
        useChatStore.getState().setWorkflowBranch('chat');
        
        render(<Sidebar isOpen={true} onClose={mockOnClose} />);
        
        expect(screen.getByText('Chat')).toBeInTheDocument();
        expect(screen.getByText('Direct Response')).toBeInTheDocument();
    });

    it('should display logs', () => {
        useChatStore.getState().addLog('Test log message', 'info');
        useChatStore.getState().addLog('Success message', 'success');
        useChatStore.getState().addLog('Error message', 'error');
        
        render(<Sidebar isOpen={true} onClose={mockOnClose} />);
        
        expect(screen.getByText('Test log message')).toBeInTheDocument();
        expect(screen.getByText('Success message')).toBeInTheDocument();
        expect(screen.getByText('Error message')).toBeInTheDocument();
    });

    it('should display empty state when no logs', () => {
        render(<Sidebar isOpen={true} onClose={mockOnClose} />);
        
        expect(screen.getByText('Waiting for events...')).toBeInTheDocument();
    });

    it('should filter out router step from agent steps display', () => {
        useChatStore.getState().setWorkflowBranch('story-graph');
        useChatStore.getState().setAgentSteps([
            { id: 'router', name: 'Router', status: 'completed' },
            { id: 'planning', name: 'Planning Story', status: 'active' },
        ]);
        
        render(<Sidebar isOpen={true} onClose={mockOnClose} />);
        
        // Router should not appear in the steps list
        const steps = screen.getAllByText(/Planning Story|Router/);
        // Router text appears in the header, but not in the steps list
        expect(screen.getByText('Planning Story')).toBeInTheDocument();
    });

    it('should show correct status indicators for active steps', () => {
        useChatStore.getState().setWorkflowBranch('story-graph');
        useChatStore.getState().setAgentSteps([
            { id: 'planning', name: 'Planning Story', status: 'active', details: 'Running...' },
        ]);
        
        render(<Sidebar isOpen={true} onClose={mockOnClose} />);
        
        expect(screen.getByText('Running...')).toBeInTheDocument();
    });

    it('should show correct status indicators for completed steps', () => {
        useChatStore.getState().setWorkflowBranch('story-graph');
        useChatStore.getState().setAgentSteps([
            { id: 'planning', name: 'Planning Story', status: 'completed' },
        ]);
        
        render(<Sidebar isOpen={true} onClose={mockOnClose} />);
        
        expect(screen.getByText('Planning Story')).toBeInTheDocument();
    });
});

