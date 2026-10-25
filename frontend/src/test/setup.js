import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// Automatically cleanup DOM after each test
afterEach(() => {
  cleanup();
});

// Mock window.Element.prototype.scrollIntoView for jsdom environment
if (typeof window !== 'undefined' && !window.Element.prototype.scrollIntoView) {
  window.Element.prototype.scrollIntoView = () => {};
}
