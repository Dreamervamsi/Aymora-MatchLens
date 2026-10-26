import React from 'react';
import { CheckCircle2, AlertCircle, Sparkles, AlertTriangle } from 'lucide-react';

/**
 * Organizes backend-provided explanation fields into clean, evidence-based sections.
 */
export const MatchExplanation = ({ evidenceSummary }) => {
  if (!evidenceSummary) return null;

  const strengths = evidenceSummary.strengths || [];
  const potentialDifferences = evidenceSummary.potential_differences || [];
  const scenarioHighlights = evidenceSummary.scenario_highlights || [];
  const missingDataWarnings = evidenceSummary.missing_data_warnings || [];

  const hasContent =
    strengths.length > 0 ||
    potentialDifferences.length > 0 ||
    scenarioHighlights.length > 0 ||
    missingDataWarnings.length > 0;

  if (!hasContent) return null;

  return (
    <div className="space-y-4 text-xs">
      {/* Why You May Be Compatible */}
      {strengths.length > 0 && (
        <div className="bg-[#F4F7F9] border border-[#BCD0E2] rounded-xl p-4">
          <h5 className="font-bold text-[#3D5A80] mb-2 flex items-center gap-1.5 text-xs">
            <CheckCircle2 className="w-4 h-4 text-[#3D5A80]" />
            Why You May Be Compatible
          </h5>
          <ul className="space-y-1.5 text-[#2B2D42]">
            {strengths.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-[#3D5A80] font-bold">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Scenario Highlights / What to Explore Together */}
      {scenarioHighlights.length > 0 && (
        <div className="bg-[#FAF6F0] border border-[#E8E3DC] rounded-xl p-4">
          <h5 className="font-bold text-[#2B2D42] mb-2 flex items-center gap-1.5 text-xs">
            <Sparkles className="w-4 h-4 text-[#E07A5F]" />
            What to Explore Together (Scenario Evidence)
          </h5>
          <ul className="space-y-1.5 text-[#5C627A]">
            {scenarioHighlights.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-[#E07A5F] font-bold">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Important Differences */}
      {potentialDifferences.length > 0 && (
        <div className="bg-[#FDF0ED] border border-[#F2C0B6] rounded-xl p-4">
          <h5 className="font-bold text-[#E07A5F] mb-2 flex items-center gap-1.5 text-xs">
            <AlertCircle className="w-4 h-4 text-[#E07A5F]" />
            Important Differences
          </h5>
          <ul className="space-y-1.5 text-[#2B2D42]">
            {potentialDifferences.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-[#E07A5F] font-bold">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Missing Data Warnings */}
      {missingDataWarnings.length > 0 && (
        <div className="bg-white border border-[#E8E3DC] rounded-xl p-3.5">
          <h5 className="font-semibold text-[#8D99AE] mb-1.5 flex items-center gap-1 text-xs">
            <AlertTriangle className="w-3.5 h-3.5" />
            Information Notes
          </h5>
          <ul className="space-y-1 text-[#5C627A]">
            {missingDataWarnings.map((item, idx) => (
              <li key={idx}>• {item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default MatchExplanation;
