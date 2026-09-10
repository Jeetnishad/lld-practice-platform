import type { ReactNode, ComponentType, InputHTMLAttributes, TextareaHTMLAttributes } from 'react';
import { Loader2, AlertCircle } from 'lucide-react';
import { Button } from './Button';

// ---------------------------------------------------------------------------
// Loading & Error Primitives
// ---------------------------------------------------------------------------

export function LoadingSpinner({ message = 'Loading…' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20" style={{ color: '#8B97A4' }}>
      <Loader2 size={22} className="spin" style={{ color: '#0EA5A0' }} />
      <p style={{ fontSize: 12, fontFamily: 'var(--font-mono)' }}>{message}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
      <div style={{
        width: 36, height: 36,
        border: '1px solid rgba(239,68,68,0.3)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#EF4444',
      }}>
        <AlertCircle size={18} />
      </div>
      <div>
        <p style={{ fontWeight: 600, color: '#E8EDF2', fontSize: 14 }}>Failed to load</p>
        <p style={{ color: '#8B97A4', fontSize: 12, marginTop: 4 }}>{message}</p>
      </div>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>Try again</Button>
      )}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  icon: Icon,
  action,
}: {
  title: string;
  description?: string;
  icon?: ComponentType<{ size?: number; className?: string }>;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16 text-center"
      style={{ border: '1px solid #1E252E', padding: 40 }}>
      {Icon && (
        <div style={{ color: '#56636F' }}>
          <Icon size={20} />
        </div>
      )}
      <div>
        <p style={{ fontWeight: 600, color: '#E8EDF2', fontSize: 14 }}>{title}</p>
        {description && (
          <p style={{ color: '#8B97A4', fontSize: 12, marginTop: 4, maxWidth: 360 }}>{description}</p>
        )}
      </div>
      {action && <div style={{ marginTop: 4 }}>{action}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page Layout & Headers
// ---------------------------------------------------------------------------

const maxWidthMap: Record<string, string> = {
  '4xl': '56rem',
  '5xl': '64rem',
  '6xl': '72rem',
  '7xl': '80rem',
};

export function PageLayout({ children, maxWidth = '6xl' }: { children: ReactNode; maxWidth?: string }) {
  return (
    <main style={{
      maxWidth: maxWidthMap[maxWidth] || '72rem',
      margin: '0 auto',
      padding: '60px 20px 80px',
      minHeight: '100vh',
    }}>
      {children}
    </main>
  );
}

export function SectionTitle({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4" style={{ marginBottom: 32, flexWrap: 'wrap' }}>
      <div>
        <h1 style={{
          fontSize: 22, fontWeight: 700, color: '#E8EDF2',
          letterSpacing: '-0.02em', lineHeight: 1.2,
        }}>
          {title}
        </h1>
        {subtitle && (
          <p style={{ color: '#8B97A4', fontSize: 13, marginTop: 6, maxWidth: 560 }}>{subtitle}</p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Score Ring
// ---------------------------------------------------------------------------

export function ScoreRing({ score, size = 64 }: { score: number; size?: number }) {
  const pct = Math.min(100, Math.max(0, score));
  const color = pct >= 70 ? '#22C55E' : pct >= 50 ? '#F59E0B' : '#EF4444';
  const r = size / 2 - 5;
  const circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;

  return (
    <div style={{ position: 'relative', display: 'inline-flex', width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#1E252E" strokeWidth="4" />
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke={color} strokeWidth="4"
          strokeDasharray={`${dash} ${circ - dash}`}
          strokeLinecap="butt"
          style={{ transition: 'stroke-dasharray 0.4s ease' }}
        />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{
          fontFamily: 'var(--font-mono)', fontSize: size > 70 ? 15 : 11,
          fontWeight: 700, color: '#E8EDF2',
        }}>
          {Math.round(pct)}
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Form Components
// ---------------------------------------------------------------------------

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  required?: boolean;
  error?: string;
  helperText?: string;
}

export function Input({ label, required, error, helperText, id, className = '', ...props }: InputProps) {
  return (
    <div style={{ width: '100%' }}>
      {label && (
        <label htmlFor={id} className="label-mono" style={{ display: 'block', marginBottom: 6 }}>
          {label}{required && <span style={{ color: '#EF4444', marginLeft: 3 }}>*</span>}
        </label>
      )}
      <input
        id={id}
        aria-required={required}
        aria-invalid={!!error}
        className={className}
        style={{
          width: '100%',
          background: '#0C0F13',
          border: `1px solid ${error ? '#EF4444' : '#1E252E'}`,
          padding: '7px 12px',
          fontSize: 13,
          color: '#E8EDF2',
          outline: 'none',
          transition: 'border-color 0.15s',
          fontFamily: 'var(--font-sans)',
        }}
        onFocus={e => { e.currentTarget.style.borderColor = error ? '#EF4444' : '#0EA5A0'; }}
        onBlur={e => { e.currentTarget.style.borderColor = error ? '#EF4444' : '#1E252E'; }}
        {...props}
      />
      {error ? (
        <p style={{ fontSize: 11, color: '#EF4444', marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
          <AlertCircle size={11} /> {error}
        </p>
      ) : helperText ? (
        <p style={{ fontSize: 11, color: '#56636F', marginTop: 4 }}>{helperText}</p>
      ) : null}
    </div>
  );
}

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  required?: boolean;
  error?: string;
  helperText?: string;
}

export function Textarea({ label, required, error, helperText, id, className = '', rows = 4, ...props }: TextareaProps) {
  return (
    <div style={{ width: '100%' }}>
      {label && (
        <label htmlFor={id} className="label-mono" style={{ display: 'block', marginBottom: 6 }}>
          {label}{required && <span style={{ color: '#EF4444', marginLeft: 3 }}>*</span>}
        </label>
      )}
      <textarea
        id={id}
        rows={rows}
        aria-required={required}
        aria-invalid={!!error}
        className={className}
        style={{
          width: '100%',
          background: '#0C0F13',
          border: `1px solid ${error ? '#EF4444' : '#1E252E'}`,
          padding: '7px 12px',
          fontSize: 12,
          color: '#E8EDF2',
          outline: 'none',
          transition: 'border-color 0.15s',
          fontFamily: 'var(--font-mono)',
          resize: 'vertical',
          lineHeight: 1.65,
        }}
        onFocus={e => { e.currentTarget.style.borderColor = error ? '#EF4444' : '#0EA5A0'; }}
        onBlur={e => { e.currentTarget.style.borderColor = error ? '#EF4444' : '#1E252E'; }}
        {...props}
      />
      {error ? (
        <p style={{ fontSize: 11, color: '#EF4444', marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
          <AlertCircle size={11} /> {error}
        </p>
      ) : helperText ? (
        <p style={{ fontSize: 11, color: '#56636F', marginTop: 4 }}>{helperText}</p>
      ) : null}
    </div>
  );
}

export function FormSection({
  title,
  purpose,
  required,
  action,
  children,
  id,
}: {
  title: string;
  purpose: string;
  required?: boolean;
  action?: ReactNode;
  children: ReactNode;
  id?: string;
}) {
  return (
    <section id={id} style={{ paddingTop: 28 }}>
      <div style={{
        borderLeft: '2px solid #0EA5A0',
        paddingLeft: 14,
        marginBottom: 16,
        display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12,
      }}>
        <div>
          <h2 style={{ fontSize: 13, fontWeight: 600, color: '#E8EDF2' }}>
            {title}
            {required && <span style={{ color: '#EF4444', marginLeft: 4 }}>*</span>}
          </h2>
          <p style={{ fontSize: 11, color: '#8B97A4', marginTop: 2 }}>{purpose}</p>
        </div>
        {action && <div style={{ flexShrink: 0 }}>{action}</div>}
      </div>
      {children}
    </section>
  );
}
