import React from 'react';
import { Info, AlertTriangle, ShieldCheck } from 'lucide-react';

/**
 * Renders backend-provided evidence coverage metric visually separate from compatibility scores.
 */
export const EvidenceCoverage = ({ coverage = 0.0, isLowCoverage = false }) => {
  const roundedCoverage = Math.max(0, Math.min(100, Math.round(coverage || 0)));

  return (
    <div className="bg-[#FAF6F0] border border-[#E8E3DC] rounded-xl p-4 mb-5">
      <div className="flex items-start gap-3">
        {isLowCoverage ? (
          <div className="p-2 rounded-lg bg-[#FDF0ED] border border-[#F2C0B6] text-[#E07A5F] shrink-0 mt-0.5">
            <AlertTriangle className="w-4 h-4" />
          </div>
        ) : (
          <div className="p-2 rounded-lg bg-[#F4F7F9] border border-[#BCD0E2] text-[#3D5A80] shrink-0 mt-0.5">
            <ShieldCheck className="w-4 h-4" />
          </div>
        )}

        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-[#2B2D42] flex items-center gap-1.5">
              Evidence Coverage
              <span className="text-xs font-normal text-[#5C627A]">({roundedCoverage}%)</span>
            </span>
            <span
              className={`text-xs font-bold px-2 py-0.5 rounded-full border ${
                isLowCoverage
                  ? 'bg-[#FDF0ED] border-[#F2C0B6] text-[#E07A5F]'
                  : 'bg-[#F4F7F9] border-[#BCD0E2] text-[#3D5A80]'
              }`}
            >
              {isLowCoverage ? 'Limited Data' : 'High Coverage'}
            </span>
          </div>

          <p className="text-xs text-[#5C627A] mb-2 leading-relaxed">
            Evidence coverage shows how much information was available to support this compatibility assessment.
          </p>

          <div className="w-full bg-white h-2 rounded-full overflow-hidden border border-[#E8E3DC]">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                isLowCoverage ? 'bg-[#E07A5F]' : 'bg-[#3D5A80]'
              }`}
              style={{ width: `${roundedCoverage}%` }}
              role="progressbar"
              aria-valuenow={roundedCoverage}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>

          {isLowCoverage && (
            <p className="text-xs text-[#E07A5F] mt-2 flex items-center gap-1 font-medium">
              <Info className="w-3.5 h-3.5 shrink-0" />
              This compatibility index has limited underlying evidence. Interpret with appropriate context.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default EvidenceCoverage;
