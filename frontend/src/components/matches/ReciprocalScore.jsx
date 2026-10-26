import React from 'react';
import { Sparkles, ArrowRight, ArrowLeft } from 'lucide-react';

/**
 * Visual display for Overall Reciprocal Compatibility and directional scores (A->B, B->A).
 * Expects normalized float scores [0-100] or null.
 */
export const ReciprocalScore = ({ mutualScore, directionalAtoB, directionalBtoA, candidateName = 'Candidate' }) => {
  const formatScore = (val) => {
    if (val === null || val === undefined || isNaN(val)) return 'N/A';
    return `${Math.round(val)}%`;
  };

  const getScoreColor = (val) => {
    if (val === null || val === undefined || isNaN(val)) return 'bg-[#E8E3DC] text-[#5C627A]';
    if (val >= 80) return 'bg-[#FDF0ED] border-[#F2C0B6] text-[#E07A5F]';
    if (val >= 60) return 'bg-[#F4F7F9] border-[#BCD0E2] text-[#3D5A80]';
    return 'bg-[#FAF6F0] border-[#E8E3DC] text-[#5C627A]';
  };

  const getBarWidth = (val) => {
    if (val === null || val === undefined || isNaN(val)) return '0%';
    const clamped = Math.max(0, Math.min(100, val));
    return `${clamped}%`;
  };

  const scoreAtoB = directionalAtoB?.directional_score;
  const scoreBtoA = directionalBtoA?.directional_score;

  return (
    <div className="bg-[#FAF6F0] border border-[#E8E3DC] rounded-xl p-5 mb-5">
      {/* Mutual / Reciprocal Index Header */}
      <div className="flex items-center justify-between pb-4 border-b border-[#E8E3DC]">
        <div>
          <span className="text-xs font-semibold tracking-wider text-[#3D5A80] uppercase block mb-0.5">
            Reciprocal Compatibility Index
          </span>
          <p className="text-xs text-[#5C627A]">
            Combined geometric mean considering both perspectives equally.
          </p>
        </div>
        <div className={`px-4 py-2 rounded-xl border font-bold text-2xl flex items-center gap-1.5 shadow-xs ${getScoreColor(mutualScore)}`}>
          <Sparkles className="w-5 h-5 text-[#E07A5F]" />
          <span>{formatScore(mutualScore)}</span>
        </div>
      </div>

      {/* Directional Compatibility Breakdown */}
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* A -> B (Your compatibility with candidate) */}
        <div className="bg-white p-3.5 rounded-lg border border-[#E8E3DC]">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="font-semibold text-[#2B2D42] flex items-center gap-1">
              Your compatibility with {candidateName}
              <ArrowRight className="w-3.5 h-3.5 text-[#E07A5F]" />
            </span>
            <span className="font-bold text-[#E07A5F]">{formatScore(scoreAtoB)}</span>
          </div>
          <div className="w-full bg-[#FAF6F0] h-2 rounded-full overflow-hidden border border-[#E8E3DC]">
            <div
              className="bg-[#E07A5F] h-full rounded-full transition-all duration-500"
              style={{ width: getBarWidth(scoreAtoB) }}
              role="progressbar"
              aria-valuenow={scoreAtoB ?? 0}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
        </div>

        {/* B -> A (Candidate's compatibility with you) */}
        <div className="bg-white p-3.5 rounded-lg border border-[#E8E3DC]">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="font-semibold text-[#2B2D42] flex items-center gap-1">
              {candidateName}&apos;s compatibility with you
              <ArrowLeft className="w-3.5 h-3.5 text-[#3D5A80]" />
            </span>
            <span className="font-bold text-[#3D5A80]">{formatScore(scoreBtoA)}</span>
          </div>
          <div className="w-full bg-[#FAF6F0] h-2 rounded-full overflow-hidden border border-[#E8E3DC]">
            <div
              className="bg-[#3D5A80] h-full rounded-full transition-all duration-500"
              style={{ width: getBarWidth(scoreBtoA) }}
              role="progressbar"
              aria-valuenow={scoreBtoA ?? 0}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReciprocalScore;
