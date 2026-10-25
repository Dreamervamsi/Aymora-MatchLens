import { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { Button } from '../ui/Button';

/**
 * Sticky chat message composer.
 * Supports multiline input, auto-height resizing, Enter to send, Shift+Enter for newline,
 * double-submission prevention, and draft message retention on failure.
 */
export const ChatComposer = ({
  onSendMessage,
  disabled = false,
  isLoading = false,
  placeholder = 'Type your response here...',
  initialValue = '',
}) => {
  const [message, setMessage] = useState(initialValue);
  const textareaRef = useRef(null);

  useEffect(() => {
    setMessage(initialValue);
  }, [initialValue]);

  // Auto-resize textarea height as user types
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 140)}px`;
    }
  }, [message]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || disabled || isLoading) return;

    onSendMessage(trimmed);
    setMessage('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white border border-[#E8E3DC] rounded-2xl p-2 sm:p-3 shadow-xs flex items-end gap-2 transition-all focus-within:border-[#E07A5F] focus-within:ring-2 focus-within:ring-[#E07A5F]/10"
    >
      <textarea
        ref={textareaRef}
        rows={1}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled || isLoading}
        placeholder={placeholder}
        className="flex-1 bg-transparent border-0 text-sm text-[#2B2D42] placeholder-[#A0A4B8] resize-none focus:outline-none p-2 min-h-[40px] max-h-[140px] leading-relaxed disabled:opacity-50"
      />

      <Button
        type="submit"
        size="md"
        disabled={!message.trim() || disabled || isLoading}
        className="shrink-0 rounded-xl px-4 py-2.5"
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin text-white" />
        ) : (
          <Send className="w-4 h-4 text-white" />
        )}
      </Button>
    </form>
  );
};

export default ChatComposer;
