import '@testing-library/jest-dom';
import { expect, afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

// Mock scrollIntoView for jsdom
Element.prototype.scrollIntoView = vi.fn();

// Polyfill CustomEvent for jsdom
if (typeof window !== 'undefined' && typeof window.CustomEvent === 'undefined') {
    (window as any).CustomEvent = class CustomEvent extends Event {
        detail: any;
        constructor(type: string, options?: { detail?: any }) {
            super(type, options);
            this.detail = options?.detail || null;
        }
    };
}

// Cleanup after each test
afterEach(() => {
    cleanup();
});

