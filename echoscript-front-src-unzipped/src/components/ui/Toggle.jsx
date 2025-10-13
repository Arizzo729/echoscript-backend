// ✅ EchoScript.AI — Final Enhanced Universal Toggle.jsx
import React, { useState, useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import { motion } from 'framer-motion';
import { twMerge } from 'tailwind-merge';

/**
 * A reliable, accessible, animated toggle switch
 * - Works across all pages and contexts
 * - Syncs with external state if needed
 * - Can trigger custom callbacks
 * - Includes fallbacks and safe error handling
 */
export default function Toggle({
  checked = false,
  onChange = () => {},
  label = '',
  disabled = false,
  size = 'md',
  className = '',
  controlled = false,
  syncExternal = null,
}) {
  const [isOn, setIsOn] = useState(!!checked);
  const prevExternal = useRef(checked);

  useEffect(() => {
    if (controlled && syncExternal !== null && syncExternal !== prevExternal.current) {
      setIsOn(!!syncExternal);
      prevExternal.current = syncExternal;
    }
  }, [controlled, syncExternal]);

  const handleToggle = () => {
    if (disabled) return;
    const newState = !isOn;
    setIsOn(newState);
    onChange(newState);
  };

  const sizes = {
    sm: {
      width: 'w-9',
      height: 'h-5',
      circle: 'w-4 h-4',
    },
    md: {
      width: 'w-11',
      height: 'h-6',
      circle: 'w-5 h-5',
    },
    lg: {
      width: 'w-14',
      height: 'h-7',
      circle: 'w-6 h-6',
    },
  };

  const { width, height, circle } = sizes[size] || sizes.md;

  return (
    <div
      className={twMerge(
        'inline-flex items-center space-x-2 select-none',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
    >
      {label && <span className="text-sm text-white whitespace-nowrap">{label}</span>}
      <button
        type="button"
        role="switch"
        aria-checked={isOn}
        aria-label={label || 'Toggle'}
        disabled={disabled}
        onClick={handleToggle}
        className={twMerge(
          'relative inline-flex items-center rounded-full transition-colors duration-300 ease-in-out focus:outline-none',
          width,
          height,
          isOn ? 'bg-teal-500' : 'bg-zinc-600'
        )}
      >
        <motion.span
          className={twMerge(
            'inline-block transform rounded-full bg-white shadow-md',
            circle
          )}
          layout
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        />
      </button>
    </div>
  );
}

Toggle.propTypes = {
  checked: PropTypes.bool,
  onChange: PropTypes.func,
  label: PropTypes.string,
  disabled: PropTypes.bool,
  size: PropTypes.oneOf(['sm', 'md', 'lg']),
  className: PropTypes.string,
  controlled: PropTypes.bool,
  syncExternal: PropTypes.bool,
};
