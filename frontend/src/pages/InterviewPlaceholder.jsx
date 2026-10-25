import React from 'react';
import { Compass, Clock, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card, Button, Badge } from '../components/ui';

/**
 * Placeholder component for upcoming Conversational Onboarding interview route (/interview).
 */
export const InterviewPlaceholder = () => {
  return (
    <div className="max-w-2xl mx-auto w-full flex-1 flex flex-col justify-center items-center py-12">
      <Card className="text-center p-8 md:p-12 w-full">
        <div className="w-16 h-16 rounded-2xl bg-[#FDF0ED] border border-[#F2C0B6] text-[#E07A5F] flex items-center justify-center mx-auto mb-6">
          <Compass className="w-8 h-8" />
        </div>
        
        <Badge variant="stone" className="mb-4">
          Upcoming Feature — Phase 7.2
        </Badge>

        <h1 className="text-2xl font-bold text-[#2B2D42] tracking-tight mb-3">
          Conversational Onboarding
        </h1>

        <p className="text-sm text-[#5C627A] max-w-md mx-auto mb-8 leading-relaxed">
          The interactive AI interview experience will be implemented in the next phase. Here, users will engage in a guided conversation to express their values, relationship goals, and personal preferences.
        </p>

        <div className="p-4 bg-[#FAF6F0] rounded-xl border border-[#E8E3DC] text-xs text-[#5C627A] flex items-center gap-3 mb-8 text-left">
          <Clock className="w-5 h-5 text-[#E07A5F] shrink-0" />
          <span>
            API endpoints for starting sessions (<code className="bg-white px-1 py-0.5 rounded border border-[#E8E3DC] text-[#2B2D42]">POST /api/v1/interview/start</code>) and processing turns are ready in the backend.
          </span>
        </div>

        <Link to="/">
          <Button variant="secondary" icon={ArrowRight}>
            Back to Welcome Page
          </Button>
        </Link>
      </Card>
    </div>
  );
};

export default InterviewPlaceholder;
