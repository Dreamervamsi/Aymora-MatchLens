import React from 'react';
import { ChevronDown, ChevronUp, Sparkles } from 'lucide-react';
import { Card, Badge, Button } from '../ui';
import ReciprocalScore from './ReciprocalScore';
import CompatibilityBreakdown from './CompatibilityBreakdown';
import EvidenceCoverage from './EvidenceCoverage';
import MatchExplanation from './MatchExplanation';

/**
 * Candidate Initials for neutral fallback avatar.
 */
const getInitials = (userBId) => {
  if (!userBId) return 'C';
  const clean = userBId.replace(/_\d+$/, '').replace(/[_-]/g, ' ');
  const parts = clean.split(' ').filter(Boolean);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return clean.substring(0, 2).toUpperCase();
};

export const MatchCard = ({ match, rank = 1, isExpanded = false, onToggleExpand }) => {
  // Candidate display identity: Use backend display_name if provided; otherwise show neutral "Candidate N" label
  const candidateName = match?.display_name || `Candidate ${rank}`;
  const userBId = match?.user_b_id;
  const initials = getInitials(userBId);

  // Extract real backend attributes if available
  const mutualScore = match?.mutual_score;
  const coverage = match?.evidence_coverage;
  const isLowCoverage = match?.is_low_coverage;
  const evidenceSummary = match?.evidence_summary;

  // Extract brief highlight string from real backend explanation for collapsed state
  const topStrength = evidenceSummary?.strengths?.[0] || evidenceSummary?.scenario_highlights?.[0];

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onToggleExpand?.();
    }
  };

  return (
    <Card className="p-6 md:p-7 border-[#E8E3DC] shadow-xs hover:shadow-sm transition-all duration-200 mb-6">
      {/* Card Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-[#E8E3DC]">
        <div className="flex items-center gap-4">
          {/* Rank Badge + Avatar */}
          <div className="relative">
            <div className="w-14 h-14 rounded-2xl bg-[#FAF6F0] border border-[#E8E3DC] flex items-center justify-center font-bold text-[#3D5A80] text-lg shadow-xs">
              {initials}
            </div>
            <div className="absolute -top-2 -left-2 bg-[#E07A5F] text-white text-xs font-bold w-6 h-6 rounded-full flex items-center justify-center shadow-xs">
              #{rank}
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-lg font-bold text-[#2B2D42] tracking-tight">{candidateName}</h3>
              {userBId && <Badge variant="stone">ID: {userBId}</Badge>}
            </div>
            {topStrength && (
              <p className="text-xs text-[#5C627A] flex items-center gap-1 max-w-md line-clamp-1">
                <Sparkles className="w-3.5 h-3.5 text-[#E07A5F] shrink-0" />
                <span>{topStrength}</span>
              </p>
            )}
          </div>
        </div>

        {/* Mutual Compatibility Badge */}
        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[10px] font-semibold text-[#8D99AE] uppercase tracking-wider block">
              Reciprocal Index
            </span>
            <span className="text-xl font-extrabold text-[#E07A5F]">
              {mutualScore !== null && mutualScore !== undefined ? `${Math.round(mutualScore)}%` : 'N/A'}
            </span>
          </div>

          <Button
            variant="secondary"
            size="sm"
            onClick={onToggleExpand}
            onKeyDown={handleKeyDown}
            aria-expanded={isExpanded}
            aria-label={`${isExpanded ? 'Hide' : 'View'} Compatibility Details for ${candidateName}`}
            icon={isExpanded ? ChevronUp : ChevronDown}
            className="shrink-0"
          >
            {isExpanded ? 'Hide Details' : 'View Compatibility Details'}
          </Button>
        </div>
      </div>

      {/* Primary Reciprocal Score Indicator (Always visible) */}
      <div className="pt-5">
        <ReciprocalScore
          mutualScore={mutualScore}
          directionalAtoB={match?.directional_a_to_b}
          directionalBtoA={match?.directional_b_to_a}
          candidateName={candidateName}
        />
      </div>

      {/* Expandable Breakdown Section */}
      {isExpanded && (
        <div className="pt-4 border-t border-[#E8E3DC] animate-fadeIn">
          {/* Evidence Coverage */}
          <EvidenceCoverage coverage={coverage} isLowCoverage={isLowCoverage} />

          {/* Dimension-level breakdown */}
          <CompatibilityBreakdown
            directionalAtoB={match?.directional_a_to_b}
            directionalBtoA={match?.directional_b_to_a}
            candidateName={candidateName}
          />

          {/* Explanations & Evidence */}
          <MatchExplanation evidenceSummary={evidenceSummary} />
        </div>
      )}
    </Card>
  );
};

export default MatchCard;
