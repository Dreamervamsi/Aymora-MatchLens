import React from 'react';
import { Layers, ShieldCheck, Clock, CheckCircle } from 'lucide-react';
import { Badge } from '../ui';

export const AssessmentHeader = ({ status, currentStage, userId }) => {
  const getStatusBadge = () => {
    if (status === 'completed' || currentStage === 'completed') {
      return (
        <Badge variant="success" className="gap-1.5 py-1 px-3">
          <CheckCircle className="w-3.5 h-3.5" />
          Assessment Completed
        </Badge>
      );
    }
    if (status === 'ready_for_review' || currentStage === 'review') {
      return (
        <Badge variant="rose" className="gap-1.5 py-1 px-3">
          <ShieldCheck className="w-3.5 h-3.5" />
          Ready for Review
        </Badge>
      );
    }
    return (
      <Badge variant="stone" className="gap-1.5 py-1 px-3">
        <Clock className="w-3.5 h-3.5" />
        Assessment In Progress
      </Badge>
    );
  };

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
      <div>
        <div className="flex items-center gap-2.5 mb-2">
          {getStatusBadge()}
          {userId && typeof userId === 'string' && (
            <span className="text-xs text-[#A0A4B8] font-mono">
              ID: {userId.substring(0, 12)}
            </span>
          )}
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-[#2B2D42] tracking-tight flex items-center gap-2.5">
          <Layers className="w-7 h-7 text-[#E07A5F]" />
          Scenario Assessment
        </h1>
        <p className="text-sm text-[#5C627A] mt-1">
          Evaluate real-world relationship decisions across two distinct perspectives: your behavior and your ideal partner.
        </p>
      </div>
    </div>
  );
};

export default AssessmentHeader;
