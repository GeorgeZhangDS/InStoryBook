import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import React from 'react';
import App from '@/App';

// Mock all page components
vi.mock('@/pages/Home', () => ({
    default: () => <div data-testid="home-page">Home Page</div>,
}));

vi.mock('@/pages/Generate', () => ({
    default: () => <div data-testid="generate-page">Generate Page</div>,
}));

// Don't mock Layout, use the real one to test routing

describe('App Component', () => {
    it('should render home page on root route', () => {
        render(
            <MemoryRouter initialEntries={['/']}>
                <App />
            </MemoryRouter>
        );
        
        expect(screen.getByTestId('home-page')).toBeInTheDocument();
    });

    it('should render generate page on /chat route', () => {
        render(
            <MemoryRouter initialEntries={['/chat']}>
                <App />
            </MemoryRouter>
        );
        
        expect(screen.getByTestId('generate-page')).toBeInTheDocument();
    });

    it('should render home page on unknown routes', () => {
        render(
            <MemoryRouter initialEntries={['/unknown-route']}>
                <App />
            </MemoryRouter>
        );
        
        expect(screen.getByTestId('home-page')).toBeInTheDocument();
    });

    it('should render correct page for each route', () => {
        const { unmount } = render(
            <MemoryRouter initialEntries={['/']}>
                <App />
            </MemoryRouter>
        );
        
        expect(screen.getByTestId('home-page')).toBeInTheDocument();
        unmount();
        
        render(
            <MemoryRouter initialEntries={['/chat']}>
                <App />
            </MemoryRouter>
        );
        
        expect(screen.getByTestId('generate-page')).toBeInTheDocument();
    });
});

