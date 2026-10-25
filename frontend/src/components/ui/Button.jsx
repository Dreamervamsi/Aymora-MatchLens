import React from 'react';

/**
 * Reusable minimalist button with warm soft-rose primary accent, subtle hover states, and focus indicators.
 */
export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  onClick,
  className = '',
  type = 'button',
  icon: Icon,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer';

  const sizeStyles = {
    sm: 'px-3 py-1.5 text-xs gap-1.5',
    md: 'px-5 py-2.5 text-sm gap-2',
    lg: 'px-7 py-3.5 text-base gap-2.5 shadow-xs',
  };

  const variantStyles = {
    primary: 'bg-[#E07A5F] hover:bg-[#C85A3F] text-white focus:ring-[#E07A5F] shadow-sm hover:shadow-md active:scale-[0.99]',
    secondary: 'bg-[#FAF6F0] hover:bg-[#F2ECE1] text-[#2B2D42] border border-[#E8E3DC] focus:ring-[#E07A5F]',
    outline: 'bg-transparent hover:bg-[#FDF0ED] text-[#E07A5F] border border-[#E07A5F] focus:ring-[#E07A5F]',
    ghost: 'bg-transparent hover:bg-[#FAF6F0] text-[#5C627A] hover:text-[#2B2D42] focus:ring-[#E07A5F]',
  };

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {Icon && <Icon className={size === 'sm' ? 'w-3.5 h-3.5' : size === 'lg' ? 'w-5 h-5' : 'w-4 h-4'} />}
      <span>{children}</span>
    </button>
  );
};

export default Button;
