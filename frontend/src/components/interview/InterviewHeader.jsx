import { InterviewStatus } from './InterviewStatus';
import { Button } from '../ui/Button';
import { FastForward, RefreshCw } from 'lucide-react';

/**
 * Interview section header component displaying session status, turn counter, and early finish trigger.
 */
export const InterviewHeader = ({
  status = 'active',
  turnCount = 0,
  onEarlyFinish,
  onStartNewSession,
  isFinished = false,
}) => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 mb-4 border-b border-[#E8E3DC]">
      <div className="flex items-center gap-3">
        <InterviewStatus status={status} />
        {turnCount > 0 && (
          <span className="text-xs font-mono text-[#5C627A] bg-white px-2.5 py-1 rounded-lg border border-[#E8E3DC]">
            Turn {turnCount}
          </span>
        )}
      </div>

      <div className="flex items-center gap-2">
        {!isFinished && onEarlyFinish && (
          <Button
            variant="ghost"
            size="sm"
            icon={FastForward}
            onClick={onEarlyFinish}
            title="Stop interview early and review profile draft"
          >
            Finish Early
          </Button>
        )}

        {onStartNewSession && (
          <Button
            variant="secondary"
            size="sm"
            icon={RefreshCw}
            onClick={onStartNewSession}
          >
            Start Fresh
          </Button>
        )}
      </div>
    </div>
  );
};

export default InterviewHeader;
