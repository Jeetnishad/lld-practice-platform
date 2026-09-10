import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, BookOpen } from 'lucide-react';
import { getAttempts, extractErrorMessage } from '../services/api';
import type { Attempt } from '../types';
import { DifficultyBadge, StatusBadge } from '../components/Badge';
import { Button } from '../components/Button';
import { PageLayout, LoadingSpinner, ErrorState, ScoreRing, EmptyState } from '../components/UI';

export function DashboardPage() {
  const navigate = useNavigate();
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = () => {
    setLoading(true);
    setError(null);
    getAttempts()
      .then(setAttempts)
      .catch(e => setError(extractErrorMessage(e)))
      .finally(() => setLoading(false));
  };

  useEffect(loadData, []);

  const completed  = attempts.filter(a => a.status === 'completed');
  const inProgress = attempts.filter(a => a.status === 'in_progress' || a.status === 'evaluating');
  const activeAttempt = inProgress[0] ?? null;

  const avgScore = completed.length
    ? Math.round(completed.reduce((s, a) => s + (a.evaluation?.overall_score ?? 0), 0) / completed.length)
    : null;

  const recentAttempts = attempts.slice(0, 5);

  return (
    <PageLayout>
      {/* ── Page heading ── */}
      <div style={{ marginBottom: 36 }}>
        <p className="label-mono" style={{ color: '#0EA5A0', marginBottom: 8 }}>
          LLD Practice Platform
        </p>
        <h1 style={{
          fontSize: 26, fontWeight: 700, color: '#E8EDF2',
          letterSpacing: '-0.025em', lineHeight: 1.2, marginBottom: 10,
        }}>
          Low-Level Design Workspace
        </h1>
        <p style={{ fontSize: 13, color: '#8B97A4', maxWidth: 520, lineHeight: 1.7 }}>
          Practice designing class architectures, interfaces, and object relationships.
          Submit structured solutions and receive rubric-based engineering feedback.
        </p>
        <div style={{ display: 'flex', gap: 8, marginTop: 20, flexWrap: 'wrap' }}>
          <Button size="md" icon={<ArrowRight size={13} />} onClick={() => navigate('/problems')}>
            Browse Problems
          </Button>
          <Button size="md" variant="outline" onClick={() => navigate('/history')}>
            Attempt History
          </Button>
        </div>
      </div>

      {/* ── Stats row ── */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
        gap: 1, background: '#1E252E', marginBottom: 40,
      }}>
        {[
          { label: 'Total Attempts', value: attempts.length },
          { label: 'Completed',      value: completed.length },
          { label: 'In Progress',    value: inProgress.length },
          { label: 'Avg Score',      value: avgScore !== null ? `${avgScore}/100` : '—' },
        ].map(({ label, value }) => (
          <div key={label} style={{
            background: '#111519', padding: '16px 20px',
          }}>
            <p className="label-mono" style={{ marginBottom: 6 }}>{label}</p>
            <p style={{
              fontFamily: 'var(--font-mono)', fontSize: 22, fontWeight: 700,
              color: '#E8EDF2', letterSpacing: '-0.02em',
            }}>{value}</p>
          </div>
        ))}
      </div>

      {/* ── Active attempt banner ── */}
      {activeAttempt && (
        <div style={{
          border: '1px solid rgba(245,158,11,0.2)',
          background: 'rgba(245,158,11,0.04)',
          padding: '14px 18px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          gap: 12, flexWrap: 'wrap', marginBottom: 32,
        }}>
          <div>
            <p className="label-mono" style={{ color: '#FBB83F', marginBottom: 3 }}>
              Active Attempt
            </p>
            <p style={{ fontSize: 13, fontWeight: 600, color: '#E8EDF2' }}>
              {activeAttempt.problem?.title} — #{activeAttempt.attempt_number}
            </p>
          </div>
          <Button
            size="sm"
            variant="outline"
            icon={<ArrowRight size={12} />}
            onClick={() => {
              if (activeAttempt.status === 'evaluating') {
                navigate(`/attempt/${activeAttempt.id}/feedback`);
              } else {
                navigate(`/attempt/${activeAttempt.id}`);
              }
            }}
          >
            Resume
          </Button>
        </div>
      )}

      {/* ── Main grid ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 32 }}
        className="lg:grid-cols-5">
        <div style={{ gridColumn: 'span 3 / span 3' }}
          className="lg:col-span-3">
          {/* Recent attempts */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <h2 style={{ fontSize: 13, fontWeight: 600, color: '#E8EDF2' }}>Recent Attempts</h2>
            {attempts.length > 0 && (
              <Link to="/history" style={{
                fontSize: 11, color: '#0EA5A0', textDecoration: 'none',
                display: 'flex', alignItems: 'center', gap: 3,
              }}>
                All history <ArrowRight size={11} />
              </Link>
            )}
          </div>

          {loading ? (
            <LoadingSpinner message="Fetching attempts..." />
          ) : error ? (
            <ErrorState message={error} onRetry={loadData} />
          ) : recentAttempts.length === 0 ? (
            <EmptyState
              title="No attempts yet"
              description="Pick a problem to start your first Low-Level Design practice session."
              icon={BookOpen}
              action={<Button onClick={() => navigate('/problems')}>Browse Problems</Button>}
            />
          ) : (
            <div style={{ borderTop: '1px solid #1E252E' }}>
              {recentAttempts.map(attempt => (
                <div
                  key={attempt.id}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 16,
                    padding: '12px 0',
                    borderBottom: '1px solid #1E252E',
                    cursor: 'pointer',
                  }}
                  onClick={() => {
                    if (attempt.status === 'completed' || attempt.status === 'evaluating' || attempt.status === 'failed') {
                      navigate(`/attempt/${attempt.id}/feedback`);
                    } else {
                      navigate(`/attempt/${attempt.id}`);
                    }
                  }}
                  onMouseEnter={e => {
                    (e.currentTarget as HTMLElement).style.background = '#111519';
                    (e.currentTarget as HTMLElement).style.paddingLeft = '8px';
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLElement).style.background = 'transparent';
                    (e.currentTarget as HTMLElement).style.paddingLeft = '0px';
                  }}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: 13, fontWeight: 500, color: '#E8EDF2', marginBottom: 3 }}>
                      {attempt.problem?.title}
                    </p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#56636F' }}>
                        #{attempt.attempt_number}
                      </span>
                      {attempt.problem && <DifficultyBadge difficulty={attempt.problem.difficulty} />}
                      <StatusBadge status={attempt.status} />
                    </div>
                  </div>
                  {attempt.evaluation?.overall_score != null ? (
                    <ScoreRing score={attempt.evaluation.overall_score} size={40} />
                  ) : (
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#56636F' }}>—</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Criteria reference */}
        <div style={{ gridColumn: 'span 2 / span 2' }} className="lg:col-span-2">
          <h2 style={{ fontSize: 13, fontWeight: 600, color: '#E8EDF2', marginBottom: 14 }}>
            Evaluation Criteria
          </h2>
          <div style={{ borderTop: '1px solid #1E252E' }}>
            {[
              ['01', 'Requirement Understanding'],
              ['02', 'Class Responsibilities'],
              ['03', 'Encapsulation & Interfaces'],
              ['04', 'Coupling & Cohesion'],
              ['05', 'Abstraction / Design Patterns'],
              ['06', 'Extensibility'],
              ['07', 'Edge Cases & Testability'],
              ['08', 'Design Explanation'],
            ].map(([num, name]) => (
              <div key={num} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '9px 0', borderBottom: '1px solid #1E252E',
              }}>
                <span style={{
                  fontFamily: 'var(--font-mono)', fontSize: 10,
                  color: '#0EA5A0', minWidth: 20,
                }}>
                  {num}
                </span>
                <span style={{ fontSize: 12, color: '#8B97A4' }}>{name}</span>
                <span style={{
                  fontFamily: 'var(--font-mono)', fontSize: 10,
                  color: '#56636F', marginLeft: 'auto',
                }}>
                  10 pts
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </PageLayout>
  );
}
