import React from 'react';
import { Layers, HelpCircle } from 'lucide-react';

const DIMENSION_LABELS = {
  core_values: 'Values',
  relationship_intentions: 'Intentions',
  lifestyle_compatibility: 'Lifestyle',
  communication_preferences: 'Communication',
  shared_interests: 'Interests',
};

/**
 * Dimension-level compatibility breakdown comparison.
 */
export const CompatibilityBreakdown = ({ directionalAtoB, directionalBtoA, candidateName = 'Candidate' }) => {
  const dimScoresAtoB = directionalAtoB?.dimension_scores || {};
  const dimScoresBtoA = directionalBtoA?.dimension_scores || {};

  const allDimensions = Object.keys(DIMENSION_LABELS);

  const formatScore = (dimObj) => {
    if (!dimObj || !dimObj.has_sufficient_data || dimObj.score === null || dimObj.score === undefined || isNaN(dimObj.score)) {
      return null;
    }
    return Math.round(dimObj.score);
  };

  return (
    <div className="bg-white border border-[#E8E3DC] rounded-xl p-5 mb-5">
      <div className="flex items-center gap-2 mb-4">
        <Layers className="w-4 h-4 text-[#3D5A80]" />
        <h4 className="text-sm font-bold text-[#2B2D42]">Compatibility Dimensions</h4>
      </div>

      <div className="space-y-4">
        {allDimensions.map((dimKey) => {
          const label = DIMENSION_LABELS[dimKey];
          const objAtoB = dimScoresAtoB[dimKey];
          const objBtoA = dimScoresBtoA[dimKey];

          const scoreAtoB = formatScore(objAtoB);
          const scoreBtoA = formatScore(objBtoA);

          const hasData = scoreAtoB !== null || scoreBtoA !== null;

          return (
            <div key={dimKey} className="p-3 bg-[#FAF6F0] border border-[#E8E3DC] rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-[#2B2D42]">{label}</span>
                {!hasData && (
                  <span className="text-xs text-[#8D99AE] italic flex items-center gap-1">
                    <HelpCircle className="w-3.5 h-3.5" />
                    Not enough evidence
                  </span>
                )}
              </div>

              {hasData ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  {/* A -> B score */}
                  <div className="flex items-center justify-between bg-white px-3 py-1.5 rounded border border-[#E8E3DC]">
                    <span className="text-[#5C627A]">You → {candidateName}:</span>
                    <span className="font-bold text-[#E07A5F]">
                      {scoreAtoB !== null ? `${scoreAtoB}%` : 'Not enough evidence'}
                    </span>
                  </div>

                  {/* B -> A score */}
                  <div className="flex items-center justify-between bg-white px-3 py-1.5 rounded border border-[#E8E3DC]">
                    <span className="text-[#5C627A]">{candidateName} → You:</span>
                    <span className="font-bold text-[#3D5A80]">
                      {scoreBtoA !== null ? `${scoreBtoA}%` : 'Not enough evidence'}
                    </span>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-[#5C627A] bg-white px-3 py-2 rounded border border-[#E8E3DC]">
                  Not enough evidence was available to score this dimension.
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CompatibilityBreakdown;
