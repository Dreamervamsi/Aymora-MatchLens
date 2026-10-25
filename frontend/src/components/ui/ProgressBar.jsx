import React from 'react';

/**
 * Reusable smooth step progress bar indicator.
 */
export const ProgressBar = ({
  progress = 0, // 0 to 100
  label,
  stepText,
  className = '',
}) => {
  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <div className={`w-full flex flex-col gap-1.5 ${className}`}>
      {(label || stepText) && (
        <div className="flex justify-between items-center text-xs font-medium text-[#5C627A]">
          {label && <span>{label}</span>}
          {stepText && <span className="text-[#E07A5F] font-semibold">{stepText}</span>}
        </div>
      )}
      <div className="w-full bg-[#E8E3DC] h-2 rounded-full overflow-hidden">
        <div
          className="bg-[#E07A5F] h-full transition-all duration-300 ease-out rounded-full"
          style={{ width: `${clampedProgress}%` }}
        />
      </div>
    </div>
  );
};

export default ProgressBar;
