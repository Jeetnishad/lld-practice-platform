import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: ReactNode;
  children: ReactNode;
}

const variantStyles: Record<string, React.CSSProperties> = {
  primary: {
    background: '#0EA5A0',
    color: '#0C0F13',
    border: '1px solid #0EA5A0',
    fontWeight: 600,
  },
  secondary: {
    background: '#171B21',
    color: '#E8EDF2',
    border: '1px solid #1E252E',
    fontWeight: 500,
  },
  danger: {
    background: 'rgba(239,68,68,0.12)',
    color: '#EF4444',
    border: '1px solid rgba(239,68,68,0.3)',
    fontWeight: 500,
  },
  ghost: {
    background: 'transparent',
    color: '#8B97A4',
    border: '1px solid transparent',
    fontWeight: 500,
  },
  outline: {
    background: 'transparent',
    color: '#E8EDF2',
    border: '1px solid #2A3340',
    fontWeight: 500,
  },
};

const sizeStyles: Record<string, React.CSSProperties> = {
  sm: { padding: '4px 10px', fontSize: 11 },
  md: { padding: '7px 14px', fontSize: 12 },
  lg: { padding: '9px 18px', fontSize: 13 },
};

const hoverBg: Record<string, string> = {
  primary: '#0D9490',
  secondary: '#1C2028',
  danger: 'rgba(239,68,68,0.2)',
  ghost: '#171B21',
  outline: '#171B21',
};

import React from 'react';

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  icon,
  children,
  className = '',
  type = 'button',
  style,
  ...props
}: ButtonProps) {
  const [hovered, setHovered] = React.useState(false);

  const baseStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    cursor: disabled || loading ? 'not-allowed' : 'pointer',
    opacity: disabled || loading ? 0.5 : 1,
    transition: 'background 0.15s, opacity 0.15s',
    userSelect: 'none',
    outline: 'none',
    whiteSpace: 'nowrap',
    fontFamily: 'var(--font-sans)',
    letterSpacing: '0.01em',
    ...variantStyles[variant],
    ...sizeStyles[size],
    ...(hovered && !disabled && !loading
      ? { background: hoverBg[variant] }
      : {}),
    ...style,
  };

  return (
    <button
      type={type}
      style={baseStyle}
      className={className}
      disabled={disabled || loading}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      {...props}
    >
      {loading ? (
        <Loader2 size={size === 'sm' ? 11 : size === 'lg' ? 14 : 12} className="spin" />
      ) : icon ? (
        <span style={{ display: 'flex', flexShrink: 0 }}>{icon}</span>
      ) : null}
      <span>{children}</span>
    </button>
  );
}
