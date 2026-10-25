import React from 'react';

/**
 * Reusable input field with rounded styling, readable text, and focus states.
 */
export const Input = ({
  label,
  error,
  helperText,
  id,
  className = '',
  type = 'text',
  placeholder,
  value,
  onChange,
  disabled = false,
  ...props
}) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="w-full flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-xs font-semibold uppercase tracking-wider text-[#5C627A]">
          {label}
        </label>
      )}
      <input
        id={inputId}
        type={type}
        value={value}
        onChange={onChange}
        disabled={disabled}
        placeholder={placeholder}
        className={`w-full px-4 py-2.5 bg-white text-[#2B2D42] border rounded-xl text-sm placeholder-[#A0A4B8] transition-colors focus:outline-none focus:ring-2 focus:ring-[#E07A5F]/20 focus:border-[#E07A5F] disabled:bg-[#FAF6F0] disabled:cursor-not-allowed ${
          error ? 'border-red-400 focus:border-red-500 focus:ring-red-400/20' : 'border-[#E8E3DC]'
        } ${className}`}
        {...props}
      />
      {error && <p className="text-xs text-red-500 mt-0.5">{error}</p>}
      {!error && helperText && <p className="text-xs text-[#5C627A] mt-0.5">{helperText}</p>}
    </div>
  );
};

export default Input;
