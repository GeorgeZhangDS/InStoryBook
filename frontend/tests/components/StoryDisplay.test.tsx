import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import StoryDisplay from '@/components/StoryDisplay';
import { useChatStore } from '@/stores/chatStore';

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
    motion: {
        div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    },
}));

describe('StoryDisplay Component', () => {
    beforeEach(() => {
        useChatStore.getState().reset();
    });

    it('should render empty state when no chapters', () => {
        render(<StoryDisplay />);
        
        expect(screen.getByText('Story will appear here...')).toBeInTheDocument();
    });

    it('should render chapters with images', () => {
        useChatStore.getState().setChapters([
            {
                chapter_id: 1,
                title: 'Chapter 1',
                text: 'Once upon a time...',
                image_url: 'https://example.com/image1.jpg',
            },
            {
                chapter_id: 2,
                title: 'Chapter 2',
                text: 'The adventure continues...',
                image_url: 'https://example.com/image2.jpg',
            },
        ]);
        
        render(<StoryDisplay />);
        
        expect(screen.getByText('Chapter 1: Chapter 1')).toBeInTheDocument();
        expect(screen.getByText('Once upon a time...')).toBeInTheDocument();
        expect(screen.getByText('Chapter 2: Chapter 2')).toBeInTheDocument();
        expect(screen.getByText('The adventure continues...')).toBeInTheDocument();
        
        const images = screen.getAllByAltText(/Chapter \d/);
        expect(images).toHaveLength(2);
        expect(images[0]).toHaveAttribute('src', 'https://example.com/image1.jpg');
        expect(images[1]).toHaveAttribute('src', 'https://example.com/image2.jpg');
    });

    it('should render chapters without images', () => {
        useChatStore.getState().setChapters([
            {
                chapter_id: 1,
                title: 'Chapter 1',
                text: 'Story text without image',
            },
        ]);
        
        render(<StoryDisplay />);
        
        expect(screen.getByText('Chapter 1: Chapter 1')).toBeInTheDocument();
        expect(screen.getByText('Story text without image')).toBeInTheDocument();
        
        // Should show placeholder icon instead of image
        const images = screen.queryAllByAltText(/Chapter \d/);
        expect(images).toHaveLength(0);
    });

    it('should render story outline when available', () => {
        useChatStore.getState().setStoryOutline({
            style: 'adventure',
            characters: ['Rabbit', 'Fox'],
            setting: 'Forest',
            plot_summary: 'A brave rabbit goes on an adventure',
        });
        
        useChatStore.getState().setChapters([
            {
                chapter_id: 1,
                title: 'Chapter 1',
                text: 'Story text',
            },
        ]);
        
        render(<StoryDisplay />);
        
        expect(screen.getByText('Story Outline')).toBeInTheDocument();
        expect(screen.getByText(/Style:/)).toBeInTheDocument();
        expect(screen.getByText('adventure')).toBeInTheDocument();
        expect(screen.getByText(/Characters:/)).toBeInTheDocument();
        expect(screen.getByText('Rabbit, Fox')).toBeInTheDocument();
        expect(screen.getByText(/Setting:/)).toBeInTheDocument();
        expect(screen.getByText('Forest')).toBeInTheDocument();
        expect(screen.getByText(/Plot:/)).toBeInTheDocument();
        expect(screen.getByText('A brave rabbit goes on an adventure')).toBeInTheDocument();
    });

    it('should not render story outline when not available', () => {
        useChatStore.getState().setChapters([
            {
                chapter_id: 1,
                title: 'Chapter 1',
                text: 'Story text',
            },
        ]);
        
        render(<StoryDisplay />);
        
        expect(screen.queryByText('Story Outline')).not.toBeInTheDocument();
    });

    it('should render story outline with partial data', () => {
        useChatStore.getState().setStoryOutline({
            style: 'adventure',
            // Missing other fields
        });
        
        useChatStore.getState().setChapters([
            {
                chapter_id: 1,
                title: 'Chapter 1',
                text: 'Story text',
            },
        ]);
        
        render(<StoryDisplay />);
        
        expect(screen.getByText('Story Outline')).toBeInTheDocument();
        expect(screen.getByText(/Style:/)).toBeInTheDocument();
        expect(screen.getByText('adventure')).toBeInTheDocument();
        expect(screen.queryByText(/Characters:/)).not.toBeInTheDocument();
        expect(screen.queryByText(/Setting:/)).not.toBeInTheDocument();
        expect(screen.queryByText(/Plot:/)).not.toBeInTheDocument();
    });

    it('should handle image load errors gracefully', () => {
        useChatStore.getState().setChapters([
            {
                chapter_id: 1,
                title: 'Chapter 1',
                text: 'Story text',
                image_url: 'https://example.com/invalid.jpg',
            },
        ]);
        
        render(<StoryDisplay />);
        
        const image = screen.getByAltText('Chapter 1');
        expect(image).toBeInTheDocument();
        
        // Simulate image error
        fireEvent.error(image);
        
        // Image should be hidden after error
        expect(image).toHaveStyle({ display: 'none' });
    });

    it('should render multiple chapters in order', () => {
        useChatStore.getState().setChapters([
            {
                chapter_id: 1,
                title: 'First Chapter',
                text: 'First text',
            },
            {
                chapter_id: 2,
                title: 'Second Chapter',
                text: 'Second text',
            },
            {
                chapter_id: 3,
                title: 'Third Chapter',
                text: 'Third text',
            },
        ]);
        
        render(<StoryDisplay />);
        
        const chapters = screen.getAllByText(/Chapter \d:/);
        expect(chapters).toHaveLength(3);
        expect(chapters[0]).toHaveTextContent('Chapter 1: First Chapter');
        expect(chapters[1]).toHaveTextContent('Chapter 2: Second Chapter');
        expect(chapters[2]).toHaveTextContent('Chapter 3: Third Chapter');
    });
});

