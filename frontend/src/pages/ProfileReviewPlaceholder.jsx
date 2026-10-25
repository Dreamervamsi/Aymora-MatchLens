import React from 'react';
import { UserCheck, Clock, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Card, Button, Badge } from '../components/ui';

/**
 * Placeholder component for upcoming Profile Review route (/profile/review).
 */
export const ProfileReviewPlaceholder = () => {
  return (
    <div className="max-w-2xl mx-auto w-full flex-1 flex flex-col justify-center items-center py-12">
      <Card className="text-center p-8 md:p-12 w-full">
        <div className="w-16 h-16 rounded-2xl bg-[#FDF0ED] border border-[#F2C0B6] text-[#E07A5F] flex items-center justify-center mx-auto mb-6">
          <UserCheck className="w-8 h-8" />
        </div>

        <Badge variant="stone" className="mb-4">
          Upcoming Feature — Phase 7.3
        </Badge>

        <h1 className="text-2xl font-bold text-[#2B2D42] tracking-tight mb-3">
          Profile Review & Confirmation
        </h1>

        <p className="text-sm text-[#5C627A] max-w-md mx-auto mb-8 leading-relaxed">
          In this section, users review their structured profile extracted during the AI interview, verify captured preferences, and confirm their profile before proceeding to scenario assessment.
        </p>

        <div className="p-4 bg-[#FAF6F0] rounded-xl border border-[#E8E3DC] text-xs text-[#5C627A] flex items-center gap-3 mb-8 text-left">
          <Clock className="w-5 h-5 text-[#E07A5F] shrink-0" />
          <span>
            Profile confirmation endpoint (<code className="bg-white px-1 py-0.5 rounded border border-[#E8E3DC] text-[#2B2D42]">POST /api/v1/interview/:id/confirm</code>) is fully prepared in the API engine.
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

export default ProfileReviewPlaceholder;
