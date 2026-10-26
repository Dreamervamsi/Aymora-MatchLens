import React from 'react';
import { Sparkles, ArrowRight, CheckCircle2 } from 'lucide-react';
import { Card, Button, Badge } from '../ui';

export const AssessmentCompletion = ({ onNavigateToMatches }) => {
  return (
    <Card className="p-8 md:p-12 text-center border-[#F2C0B6] shadow-md max-w-2xl mx-auto w-full my-8">
      <div className="w-16 h-16 rounded-2xl bg-[#FDF0ED] border border-[#F2C0B6] text-[#E07A5F] flex items-center justify-center mx-auto mb-6">
        <CheckCircle2 className="w-8 h-8" />
      </div>

      <Badge variant="rose" className="mb-4">
        Phase 7.4 Completed
      </Badge>

      <h1 className="text-2xl sm:text-3xl font-extrabold text-[#2B2D42] tracking-tight mb-3">
        Scenario Assessment Confirmed!
      </h1>

      <p className="text-sm text-[#5C627A] max-w-md mx-auto mb-8 leading-relaxed">
        Your scenario responses for both self-behavior and ideal partner expectations have been attached to your confirmed profile.
      </p>

      <div className="p-4 bg-[#FAF6F0] rounded-2xl border border-[#E8E3DC] text-xs text-[#5C627A] flex items-center gap-3 mb-8 text-left max-w-lg mx-auto">
        <Sparkles className="w-5 h-5 text-[#E07A5F] shrink-0" />
        <span>
          You are now eligible for reciprocal profile matching and multi-dimensional Compatibility Index ranking.
        </span>
      </div>

      <Button
        variant="primary"
        icon={ArrowRight}
        onClick={onNavigateToMatches}
        className="py-3.5 px-8 shadow-md text-base"
      >
        Discover My Matches
      </Button>
    </Card>
  );
};

export default AssessmentCompletion;
