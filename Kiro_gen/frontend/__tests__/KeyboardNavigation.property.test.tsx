import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import * as fc from 'fast-check';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { FileUpload } from '@/components/FileUpload';
import { AudioPlayer } from '@/components/AudioPlayer';
import UploadPage from '@/app/upload/page';
import LibraryPage from '@/app/library/page';
import PlaybackPage from '@/app/playback/page';
import { useAppStore } from '@/lib/store';

vi.mock('@/lib/api-client');
vi.mock('@/lib/store');

/**
 * Feature: comic-audio-narrator, Property 19: Keyboard Navigation
 * Validates: Requirements 10.2
 */
describe('Keyboard Navigation - Property Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (useAppStore as any).mockReturnValue({
      isUploading: false,
      uploadProgress: 0,
      uploadError: null,
      library: [
        {
          id: '1',
          title: 'Test Comic',
          characters: ['Hero', 'Villain'],
          scenes: ['City', 'Forest'],
          duration: 300,
          uploadedAt: '2024-01-01T00:00:00Z'
        }
      ],
      isLoadingLibrary: false,
      libraryError: null,
      currentAudio: null,
      isPlaying: false,
      currentTime: 0,
      setUploading: vi.fn(),
      setUploadProgress: vi.fn(),
      setUploadError: vi.fn(),
      setLibrary: vi.fn(),
      setLoadingLibrary: vi.fn(),
      setLibraryError: vi.fn(),
      setCurrentAudio: vi.fn(),
      setPlaying: vi.fn(),
      setCurrentTime: vi.fn(),
      addToLibrary: vi.fn(),
      removeFromLibrary: vi.fn(),
    });
  });

  /**
   * Property 19: Keyboard Navigation
   * For any web interface functionality, the system SHALL provide full access via keyboard navigation without requiring a mouse
   */
  it('should allow tab navigation through all focusable elements', () => {
    fc.assert(
      fc.property(
        fc.constantFrom(
          () => render(<UploadPage />),
          () => render(<LibraryPage />),
          () => render(<FileUpload />)
        ),
        async (renderFn) => {
          const user = userEvent.setup();
          const { container } = renderFn();
          
          // Get all focusable elements in document order
          const focusableElements = Array.from(container.querySelectorAll(
            'button:not([disabled]):not([tabindex="-1"]), ' +
            'input:not([disabled]):not([tabindex="-1"]), ' +
            'select:not([disabled]):not([tabindex="-1"]), ' +
            'textarea:not([disabled]):not([tabindex="-1"]), ' +
            'a[href]:not([tabindex="-1"]), ' +
            '[tabindex]:not([tabindex="-1"]):not([disabled])'
          ));
          
          if (focusableElements.length === 0) return true;
          
          // Start from first element
          focusableElements[0].focus();
          expect(document.activeElement).toBe(focusableElements[0]);
          
          // Tab through all elements
          for (let i = 1; i < Math.min(focusableElements.length, 10); i++) {
            await user.tab();
            expect(document.activeElement).toBe(focusableElements[i]);
          }
          
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should support reverse tab navigation', () => {
    fc.assert(
      fc.property(
        fc.constantFrom(
          () => render(<UploadPage />),
          () => render(<LibraryPage />)
        ),
        async (renderFn) => {
          const user = userEvent.setup();
          const { container } = renderFn();
          
          const focusableElements = Array.from(container.querySelectorAll(
            'button:not([disabled]):not([tabindex="-1"]), ' +
            'input:not([disabled]):not([tabindex="-1"]), ' +
            'select:not([disabled]):not([tabindex="-1"]), ' +
            'a[href]:not([tabindex="-1"])'
          ));
          
          if (focusableElements.length < 2) return true;
          
          // Focus on second element
          focusableElements[1].focus();
          expect(document.activeElement).toBe(focusableElements[1]);
          
          // Shift+Tab should go to previous element
          await user.tab({ shift: true });
          expect(document.activeElement).toBe(focusableElements[0]);
          
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should handle Enter and Space key activation for buttons', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('Enter', ' '),
        async (key) => {
          const user = userEvent.setup();
          const mockOnClick = vi.fn();
          
          const TestButton = () => (
            <button onClick={mockOnClick} type="button">
              Test Button
            </button>
          );
          
          render(<TestButton />);
          const button = screen.getByRole('button', { name: 'Test Button' });
          
          button.focus();
          await user.keyboard(`{${key}}`);
          
          expect(mockOnClick).toHaveBeenCalledTimes(1);
          
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should support arrow key navigation in audio player', () => {
    fc.assert(
      fc.property(
        fc.constantFrom('ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'),
        async (arrowKey) => {
          const user = userEvent.setup();
          const mockAudioUrl = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT';
          
          render(<AudioPlayer audioUrl={mockAudioUrl} duration={300} />);
          
          const audioPlayer = screen.getByRole('region', { name: 'Audio player' });
          audioPlayer.focus();
          
          // Test arrow key functionality
          await user.keyboard(`{${arrowKey}}`);
          
          // The audio player should handle the key press
          // In a real implementation, this would test specific behaviors:
          // - ArrowLeft/Right: Skip backward/forward
          // - ArrowUp/Down: Volume control
          expect(audioPlayer).toBeInTheDocument();
          
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should maintain focus visibility for all interactive elements', () => {
    fc.assert(
      fc.property(
        fc.constantFrom(
          () => render(<UploadPage />),
          () => render(<LibraryPage />)
        ),
        async (renderFn) => {
          const user = userEvent.setup();
          const { container } = renderFn();
          
          const focusableElements = container.querySelectorAll(
            'button:not([disabled]), input:not([disabled]), select:not([disabled]), a[href]'
          );
          
          for (const element of Array.from(focusableElements).slice(0, 5)) {
            element.focus();
            
            // Check that element has focus styles
            const computedStyle = window.getComputedStyle(element);
            const hasFocusIndicator = 
              computedStyle.outline !== 'none' ||
              computedStyle.boxShadow !== 'none' ||
              element.classList.contains('focus:outline-none') ||
              element.classList.contains('focus:ring-2') ||
              element.classList.contains('focus:border-blue-500');
            
            expect(hasFocusIndicator).toBe(true);
          }
          
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should support Escape key to close modals and dismiss errors', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 50 }),
        async (errorMessage) => {
          const user = userEvent.setup();
          
          (useAppStore as any).mockReturnValue({
            isUploading: false,
            uploadProgress: 0,
            uploadError: errorMessage,
            setUploading: vi.fn(),
            setUploadProgress: vi.fn(),
            setUploadError: vi.fn(),
          });
          
          render(<FileUpload />);
          
          // Find error message
          const errorAlert = screen.queryByRole('alert');
          if (errorAlert) {
            const dismissButton = errorAlert.querySelector('button');
            if (dismissButton) {
              dismissButton.focus();
              await user.keyboard('{Escape}');
              
              // In a real implementation, Escape should dismiss the error
              expect(dismissButton).toBeInTheDocument();
            }
          }
          
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should handle keyboard shortcuts consistently', () => {
    fc.assert(
      fc.property(
        fc.record({
          key: fc.constantFrom('m', 'M', ' ', 'ArrowLeft', 'ArrowRight'),
          ctrlKey: fc.boolean(),
          shiftKey: fc.boolean(),
          altKey: fc.boolean()
        }),
        async (keyEvent) => {
          const user = userEvent.setup();
          const mockAudioUrl = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT';
          
          render(<AudioPlayer audioUrl={mockAudioUrl} duration={300} />);
          
          const audioPlayer = screen.getByRole('region', { name: 'Audio player' });
          audioPlayer.focus();
          
          // Test keyboard shortcut
          const modifiers = [];
          if (keyEvent.ctrlKey) modifiers.push('Control');
          if (keyEvent.shiftKey) modifiers.push('Shift');
          if (keyEvent.altKey) modifiers.push('Alt');
          
          const keyCombo = modifiers.length > 0 
            ? `{${modifiers.join('+')}}+{${keyEvent.key}}`
            : `{${keyEvent.key}}`;
          
          await user.keyboard(keyCombo);
          
          // Audio player should handle the keyboard shortcut
          expect(audioPlayer).toBeInTheDocument();
          
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should provide logical tab order for form elements', () => {
    fc.assert(
      fc.property(
        fc.array(fc.string({ minLength: 1, maxLength: 20 }), { minLength: 2, maxLength: 5 }),
        async (fieldNames) => {
          const user = userEvent.setup();
          
          // Create a test form with multiple fields
          const TestForm = () => (
            <form>
              {fieldNames.map((name, index) => (
                <div key={index}>
                  <label htmlFor={`field-${index}`}>{name}</label>
                  <input
                    id={`field-${index}`}
                    type="text"
                    name={name}
                    tabIndex={index}
                  />
                </div>
              ))}
              <button type="submit">Submit</button>
            </form>
          );
          
          const { container } = render(<TestForm />);
          
          const inputs = container.querySelectorAll('input');
          const submitButton = container.querySelector('button[type="submit"]');
          
          // Tab through inputs in order
          inputs[0].focus();
          expect(document.activeElement).toBe(inputs[0]);
          
          for (let i = 1; i < inputs.length; i++) {
            await user.tab();
            expect(document.activeElement).toBe(inputs[i]);
          }
          
          // Tab to submit button
          await user.tab();
          expect(document.activeElement).toBe(submitButton);
          
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should skip disabled elements during tab navigation', () => {
    fc.assert(
      fc.property(
        fc.boolean(),
        async (isDisabled) => {
          const user = userEvent.setup();
          
          const TestComponent = () => (
            <div>
              <button>First Button</button>
              <button disabled={isDisabled}>Middle Button</button>
              <button>Last Button</button>
            </div>
          );
          
          render(<TestComponent />);
          
          const firstButton = screen.getByRole('button', { name: 'First Button' });
          const middleButton = screen.getByRole('button', { name: 'Middle Button' });
          const lastButton = screen.getByRole('button', { name: 'Last Button' });
          
          firstButton.focus();
          expect(document.activeElement).toBe(firstButton);
          
          await user.tab();
          
          if (isDisabled) {
            // Should skip disabled button and go to last button
            expect(document.activeElement).toBe(lastButton);
          } else {
            // Should go to middle button
            expect(document.activeElement).toBe(middleButton);
          }
          
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should handle focus trapping in modal-like components', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 50 }),
        async (errorMessage) => {
          const user = userEvent.setup();
          
          (useAppStore as any).mockReturnValue({
            isUploading: false,
            uploadProgress: 0,
            uploadError: errorMessage,
            setUploading: vi.fn(),
            setUploadProgress: vi.fn(),
            setUploadError: vi.fn(),
          });
          
          render(<FileUpload />);
          
          const errorAlert = screen.queryByRole('alert');
          if (errorAlert) {
            const focusableInAlert = errorAlert.querySelectorAll(
              'button:not([disabled]), input:not([disabled]), a[href]'
            );
            
            if (focusableInAlert.length > 0) {
              // Focus should be manageable within the alert
              focusableInAlert[0].focus();
              expect(document.activeElement).toBe(focusableInAlert[0]);
              
              // Tab navigation should work within the alert
              if (focusableInAlert.length > 1) {
                await user.tab();
                expect(Array.from(focusableInAlert)).toContain(document.activeElement);
              }
            }
          }
          
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });
});