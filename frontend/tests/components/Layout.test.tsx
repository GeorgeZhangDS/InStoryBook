import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Layout from '@/components/Layout';

describe('Layout Component', () => {
    const renderWithRouter = (path: string) => {
        return render(
            <MemoryRouter initialEntries={[path]}>
                <Layout />
            </MemoryRouter>
        );
    };

    beforeEach(() => {
        // Clear any existing content
    });

    it('should render header and footer on non-home, non-chat routes', () => {
        renderWithRouter('/some-other-route');
        
        expect(screen.getByText('InStoryBook')).toBeInTheDocument();
        expect(screen.getByText(/© \d{4} InStoryBook/)).toBeInTheDocument();
    });

    it('should hide header and footer on home route', () => {
        renderWithRouter('/');
        
        expect(screen.queryByText('InStoryBook')).not.toBeInTheDocument();
        expect(screen.queryByText(/© \d{4} InStoryBook/)).not.toBeInTheDocument();
    });

    it('should hide header and footer on chat route', () => {
        renderWithRouter('/chat');
        
        expect(screen.queryByText('InStoryBook')).not.toBeInTheDocument();
        expect(screen.queryByText(/© \d{4} InStoryBook/)).not.toBeInTheDocument();
    });

    it('should render background blobs', () => {
        const { container } = renderWithRouter('/');
        
        // Check for blob elements (they have specific classes)
        const blobs = container.querySelectorAll('.animate-blob-1, .animate-blob-2, .animate-blob-3');
        expect(blobs.length).toBeGreaterThan(0);
    });

    it('should render main content area', () => {
        const { container } = renderWithRouter('/');
        
        const main = container.querySelector('main');
        expect(main).toBeInTheDocument();
    });

    it('should apply correct padding when header is visible', () => {
        const { container } = renderWithRouter('/some-route');
        
        const main = container.querySelector('main');
        expect(main).toHaveClass('pt-16');
    });

    it('should not apply padding when header is hidden', () => {
        const { container } = renderWithRouter('/');
        
        const main = container.querySelector('main');
        expect(main).not.toHaveClass('pt-16');
    });
});

