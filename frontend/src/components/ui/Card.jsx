import React from 'react';

/**
 * Rounded card container with soft border, warm background tint, and subtle shadow.
 */
export const Card = ({
  children,
  className = '',
  title,
  subtitle,
  footer,
  padding = 'normal',
  hover = false,
  ...props
}) => {
  const paddingStyles = {
    none: 'p-0',
    tight: 'p-4',
    normal: 'p-6 md:p-8',
    spacious: 'p-8 md:p-10',
  };

  const hoverStyle = hover ? 'hover:shadow-md hover:border-[#D1C9BE] transition-all duration-200' : '';

  return (
    <div
      className={`bg-white border border-[#E8E3DC] rounded-2xl shadow-xs text-[#2B2D42] ${paddingStyles[padding]} ${hoverStyle} ${className}`}
      {...props}
    >
      {(title || subtitle) && (
        <div className="mb-4">
          {title && <h3 className="text-lg font-semibold text-[#2B2D42] tracking-tight">{title}</h3>}
          {subtitle && <p className="text-sm text-[#5C627A] mt-1">{subtitle}</p>}
        </div>
      )}
      <div>{children}</div>
      {footer && <div className="mt-6 pt-4 border-t border-[#E8E3DC]">{footer}</div>}
    </div>
  );
};

export default Card;
