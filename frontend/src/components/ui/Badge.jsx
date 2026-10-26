import React from 'react';

/**
 * Reusable minimal badge component for step status, category tags, or topics.
 */
export const Badge = ({
  children,
  variant = 'rose',
  size = 'md',
  className = '',
  icon: Icon,
}) => {
  const variantStyles = {
    rose: 'bg-[#FDF0ED] text-[#E07A5F] border border-[#F2C0B6]',
    stone: 'bg-[#FAF6F0] text-[#5C627A] border border-[#E8E3DC]',
    sky: 'bg-[#F4F7F9] text-[#3D5A80] border border-[#BCD0E2]',
    emerald: 'bg-[#EBF7F0] text-[#2A7B4C] border border-[#C2E8D0]',
    success: 'bg-[#EBF7F0] text-[#2A7B4C] border border-[#C2E8D0]',
    neutral: 'bg-white text-[#2B2D42] border border-[#E8E3DC]',
  };

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs font-medium rounded-md gap-1',
    md: 'px-2.5 py-1 text-xs font-semibold rounded-lg gap-1.5',
    lg: 'px-3 py-1.5 text-sm font-semibold rounded-xl gap-2',
  };

  return (
    <span className={`inline-flex items-center tracking-wide ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}>
      {Icon && <Icon className="w-3.5 h-3.5" />}
      <span>{children}</span>
    </span>
  );
};

export default Badge;
