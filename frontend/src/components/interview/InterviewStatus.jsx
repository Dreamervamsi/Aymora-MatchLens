import { Badge } from '../ui/Badge';
import { Sparkles, AlertCircle, CheckCircle2, Flag } from 'lucide-react';

/**
 * Status badge component corresponding to backend InterviewStatus enum.
 * Supported values: 'active', 'awaiting_confirmation', 'ready_for_review', 'completed'
 */
export const InterviewStatus = ({ status = 'active' }) => {
  const statusMap = {
    active: {
      label: 'Active Conversation',
      variant: 'rose',
      icon: Sparkles,
    },
    awaiting_confirmation: {
      label: 'Clarification Needed',
      variant: 'neutral',
      icon: AlertCircle,
    },
    ready_for_review: {
      label: 'Ready For Review',
      variant: 'success',
      icon: CheckCircle2,
    },
    completed: {
      label: 'Profile Confirmed',
      variant: 'success',
      icon: Flag,
    },
  };

  const current = statusMap[status] || statusMap.active;

  return (
    <Badge variant={current.variant} size="md" icon={current.icon}>
      {current.label}
    </Badge>
  );
};

export default InterviewStatus;
