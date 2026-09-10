export interface BadgeProps {
  label: string;
  variant?: 'easy' | 'medium' | 'hard' | 'primary' | 'success' | 'warning' | 'danger' | 'muted' | 'ai' | 'fallback';
  size?: 'sm' | 'md';
  className?: string;
}

const variantStyles: Record<string, React.CSSProperties> = {
  easy:     { background: 'rgba(34,197,94,0.1)',  color: '#4ADE80', border: '1px solid rgba(34,197,94,0.25)' },
  medium:   { background: 'rgba(245,158,11,0.1)', color: '#FBB83F', border: '1px solid rgba(245,158,11,0.25)' },
  hard:     { background: 'rgba(239,68,68,0.1)',  color: '#F87171', border: '1px solid rgba(239,68,68,0.25)' },
  primary:  { background: 'rgba(14,165,160,0.1)', color: '#2DD4BF', border: '1px solid rgba(14,165,160,0.25)' },
  success:  { background: 'rgba(34,197,94,0.1)',  color: '#4ADE80', border: '1px solid rgba(34,197,94,0.25)' },
  warning:  { background: 'rgba(245,158,11,0.1)', color: '#FBB83F', border: '1px solid rgba(245,158,11,0.25)' },
  danger:   { background: 'rgba(239,68,68,0.1)',  color: '#F87171', border: '1px solid rgba(239,68,68,0.25)' },
  muted:    { background: '#171B21', color: '#8B97A4', border: '1px solid #1E252E' },
  ai:       { background: 'rgba(14,165,160,0.1)', color: '#2DD4BF', border: '1px solid rgba(14,165,160,0.25)' },
  fallback: { background: 'rgba(139,92,246,0.1)', color: '#A78BFA', border: '1px solid rgba(139,92,246,0.25)' },
};

import React from 'react';

export function Badge({ label, variant = 'muted', size = 'md', className = '' }: BadgeProps) {
  const sizeStyle: React.CSSProperties = size === 'sm'
    ? { padding: '1px 6px', fontSize: 9 }
    : { padding: '2px 7px', fontSize: 10 };

  return (
    <span
      className={className}
      style={{
        display: 'inline-flex', alignItems: 'center',
        fontFamily: 'var(--font-mono)', fontWeight: 600,
        letterSpacing: '0.07em', textTransform: 'uppercase',
        userSelect: 'none',
        ...variantStyles[variant],
        ...sizeStyle,
      }}
    >
      {label}
    </span>
  );
}

export function DifficultyBadge({ difficulty }: { difficulty: string }) {
  const labels: Record<string, string> = { easy: 'Easy', medium: 'Medium', hard: 'Hard' };
  const variant = (difficulty?.toLowerCase() as 'easy' | 'medium' | 'hard') || 'muted';
  return <Badge label={labels[difficulty] || difficulty} variant={variant} />;
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; variant: BadgeProps['variant'] }> = {
    in_progress: { label: 'In Progress', variant: 'warning' },
    submitted:   { label: 'Submitted',   variant: 'primary' },
    evaluating:  { label: 'Evaluating',  variant: 'primary' },
    completed:   { label: 'Completed',   variant: 'success' },
    failed:      { label: 'Failed',      variant: 'danger'  },
  };
  const config = map[status] || { label: status, variant: 'muted' };
  return <Badge label={config.label} variant={config.variant} />;
}
