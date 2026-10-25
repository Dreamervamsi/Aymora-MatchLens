import { HeartHandshake, User, CheckCircle2, AlertCircle } from 'lucide-react';
import { Badge } from '../ui/Badge';

/**
 * Reusable chat message bubble component.
 * Distinguishes user messages (right-aligned, soft rose) and assistant messages (left-aligned, warm card).
 */
export const ChatMessage = ({
  role = 'assistant',
  content = '',
  timestamp,
  newlyExtracted = [],
  pendingConfirmations = [],
  onConfirmClick,
  onRejectClick,
  isInteractive = false,
  isLoading = false,
}) => {
  const isUser = role === 'user';

  const formattedTime = timestamp
    ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : null;

  return (
    <div className={`flex gap-3 my-3 w-full ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar Icon */}
      <div
        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-semibold shadow-2xs ${
          isUser
            ? 'bg-[#E07A5F] text-white'
            : 'bg-[#FAF6F0] text-[#E07A5F] border border-[#E8E3DC]'
        }`}
      >
        {isUser ? <User className="w-4 h-4" /> : <HeartHandshake className="w-4 h-4" />}
      </div>

      {/* Message Content Bubble */}
      <div className={`flex flex-col max-w-[82%] sm:max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? 'bg-[#E07A5F] text-white rounded-tr-xs shadow-xs font-normal'
              : 'bg-white text-[#2B2D42] border border-[#E8E3DC] rounded-tl-xs shadow-2xs'
          }`}
        >
          <p className="whitespace-pre-wrap break-words">{content}</p>

          {/* Newly Extracted Field Tags */}
          {!isUser && newlyExtracted && newlyExtracted.length > 0 && (
            <div className="mt-3 pt-2.5 border-t border-[#E8E3DC] flex flex-wrap gap-1.5 items-center">
              <span className="text-[11px] font-semibold text-[#5C627A] flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-[#2A7B4C]" />
                Captured:
              </span>
              {newlyExtracted.map((field, idx) => (
                <Badge key={idx} variant="success" size="sm">
                  {field.replace(/^(attributes|expectations|dealbreakers)\./, '')}
                </Badge>
              ))}
            </div>
          )}

          {/* Pending Confirmations Prompt Card */}
          {!isUser && pendingConfirmations && pendingConfirmations.length > 0 && (
            <div className="mt-3 p-3 bg-[#FAF6F0] rounded-xl border border-[#F2C0B6] flex flex-col gap-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-[#E07A5F]">
                <AlertCircle className="w-4 h-4" />
                <span>Confirmation Requested</span>
              </div>
              <p className="text-xs text-[#5C627A]">
                {pendingConfirmations[0].reasoning || 'Please confirm if this proposed value is accurate:'}
              </p>
              <div className="text-xs font-medium bg-white px-3 py-1.5 rounded-lg border border-[#E8E3DC] text-[#2B2D42]">
                <span className="font-semibold">{pendingConfirmations[0].field_name}:</span>{' '}
                {String(pendingConfirmations[0].proposed_value)}
              </div>
              {onConfirmClick && isInteractive ? (
                <div className="flex gap-2 mt-1">
                  <button
                    type="button"
                    disabled={isLoading}
                    onClick={() => onConfirmClick('Yes, that is correct.')}
                    className="flex-1 py-1 px-2.5 bg-[#E07A5F] hover:bg-[#C85A3F] text-white rounded-lg text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50"
                  >
                    Yes, Confirm
                  </button>
                  <button
                    type="button"
                    disabled={isLoading}
                    onClick={() => {
                      if (onRejectClick) {
                        onRejectClick(pendingConfirmations[0]);
                      } else {
                        onConfirmClick('No, that is not correct.');
                      }
                    }}
                    className="flex-1 py-1 px-2.5 bg-white hover:bg-[#F2ECE1] text-[#2B2D42] border border-[#E8E3DC] rounded-lg text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50"
                  >
                    No, Correct
                  </button>
                </div>
              ) : (
                <div className="text-[11px] font-medium text-[#A0A4B8] italic mt-1">
                  Confirmation recorded
                </div>
              )}
            </div>
          )}
        </div>

        {/* Timestamp */}
        {formattedTime && (
          <span className="text-[10px] text-[#A0A4B8] mt-1 px-1">{formattedTime}</span>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
