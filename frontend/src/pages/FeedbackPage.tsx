import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { RefreshCw, RotateCcw, ChevronLeft, CheckCircle2, AlertTriangle, Lightbulb, Quote, ArrowRight } from 'lucide-react';
import { getAttempt, getEvaluation, retryEvaluation, extractErrorMessage } from '../services/api';
import type { Attempt, Evaluation, RubricCriterion } from '../types';
import { Button } from '../components/Button';
import { Badge, StatusBadge } from '../components/Badge';
import { PageLayout, LoadingSpinner, ErrorState, ScoreRing } from '../components/UI';

function scoreColor(score: number, max = 10): string {
  const pct = (score / max) * 100;
  if (pct >= 70) return '#22C55E';
  if (pct >= 50) return '#F59E0B';
  return '#EF4444';
}

function confidenceVariant(c: string): 'success' | 'warning' | 'muted' {
  if (c === 'high') return 'success';
  if (c === 'medium') return 'warning';
  return 'muted';
}

// ---------------------------------------------------------------------------
// Criterion Row (collapsible)
// ---------------------------------------------------------------------------

function CriterionRow({ criterion, index }: { criterion: RubricCriterion; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const pct = (criterion.score / criterion.max_score) * 100;
  const color = scoreColor(criterion.score, criterion.max_score);

  return (
    <div style={{ borderBottom: '1px solid #1E252E' }} className="animate-fade-in">
      {/* Header row */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', gap: 12,
          padding: '12px 0', background: 'none', border: 'none',
          cursor: 'pointer', textAlign: 'left', transition: 'background 0.12s',
        }}
        onMouseEnter={e => (e.currentTarget.style.background = '#111519')}
        onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
      >
        {/* Index */}
        <span style={{
          fontFamily: 'var(--font-mono)', fontSize: 10, color: '#56636F',
          minWidth: 24, flexShrink: 0,
        }}>
          {String(index + 1).padStart(2, '0')}
        </span>

        {/* Name & confidence */}
        <div style={{ flex: 1, minWidth: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13, fontWeight: 500, color: '#E8EDF2' }}>
            {criterion.name}
          </span>
          <Badge label={criterion.confidence} variant={confidenceVariant(criterion.confidence)} size="sm" />
        </div>

        {/* Score + bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
          {/* Inline bar */}
          <div style={{
            width: 60, height: 3,
            background: '#1E252E', flexShrink: 0, display: 'none',
          }} className="sm:block">
            <div style={{
              height: '100%', width: `${pct}%`,
              background: color, transition: 'width 0.4s ease',
            }} />
          </div>
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: 14,
            fontWeight: 700, color,
          }}>
            {criterion.score}
            <span style={{ fontWeight: 400, color: '#56636F', fontSize: 10 }}>/{criterion.max_score}</span>
          </span>
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: 9, color: '#56636F',
          }}>
            {expanded ? '▲' : '▼'}
          </span>
        </div>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div style={{
          padding: '12px 0 20px 36px',
          display: 'flex', flexDirection: 'column', gap: 12,
        }} className="animate-fade-in">
          {criterion.evidence && (
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <Quote size={13} style={{ color: '#0EA5A0', marginTop: 1, flexShrink: 0 }} />
              <div>
                <p className="label-mono" style={{ marginBottom: 4 }}>Evidence in Submission</p>
                <p style={{
                  fontSize: 12, color: '#C5CDD6', lineHeight: 1.65,
                  background: '#111519', border: '1px solid #1E252E',
                  padding: '8px 12px',
                }}>
                  {criterion.evidence}
                </p>
              </div>
            </div>
          )}
          {criterion.concern && (
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <AlertTriangle size={13} style={{ color: '#F59E0B', marginTop: 1, flexShrink: 0 }} />
              <div>
                <p className="label-mono" style={{ color: '#F59E0B', marginBottom: 4 }}>Concern / Gap</p>
                <p style={{ fontSize: 12, color: '#C5CDD6', lineHeight: 1.65 }}>{criterion.concern}</p>
              </div>
            </div>
          )}
          {criterion.suggestion && (
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <Lightbulb size={13} style={{ color: '#22C55E', marginTop: 1, flexShrink: 0 }} />
              <div>
                <p className="label-mono" style={{ color: '#22C55E', marginBottom: 4 }}>Suggestion</p>
                <p style={{ fontSize: 12, color: '#C5CDD6', lineHeight: 1.65 }}>{criterion.suggestion}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main FeedbackPage
// ---------------------------------------------------------------------------

export function FeedbackPage() {
  const { id: attemptId } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [attempt, setAttempt]     = useState<Attempt | null>(null);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState<string | null>(null);
  const [retrying, setRetrying]   = useState(false);
  const [polling, setPolling]     = useState(false);

  const loadData = useCallback(async () => {
    if (!attemptId) return;
    try {
      const [a, ev] = await Promise.all([
        getAttempt(attemptId),
        getEvaluation(attemptId).catch(() => null),
      ]);
      setAttempt(a);
      setEvaluation(ev);
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [attemptId]);

  useEffect(() => { loadData(); }, [loadData]);

  useEffect(() => {
    if (!evaluation || evaluation.status === 'completed' || evaluation.status === 'failed') return;
    const timer = setTimeout(() => {
      setPolling(true);
      loadData().finally(() => setPolling(false));
    }, 2500);
    return () => clearTimeout(timer);
  }, [evaluation, loadData]);

  const handleRetry = async () => {
    if (!attemptId) return;
    setRetrying(true);
    try {
      const ev = await retryEvaluation(attemptId);
      setEvaluation(ev);
      setAttempt(prev => prev ? { ...prev, status: 'evaluating' } : prev);
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setRetrying(false);
    }
  };

  const handleTryAgain = () => {
    if (!attempt?.problem_id) return;
    navigate(`/problems/${attempt.problem_id}`);
  };

  if (loading) return <PageLayout><LoadingSpinner message="Fetching feedback…" /></PageLayout>;
  if (error)   return <PageLayout><ErrorState message={error} onRetry={loadData} /></PageLayout>;

  const isEvaluating = !evaluation || evaluation.status === 'pending' || evaluation.status === 'evaluating';
  const isFailed     = evaluation?.status === 'failed';
  const isCompleted  = evaluation?.status === 'completed';

  return (
    <PageLayout maxWidth="4xl">
      {/* Back */}
      <button
        onClick={() => navigate('/history')}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 4,
          color: '#8B97A4', fontSize: 12, background: 'none', border: 'none',
          cursor: 'pointer', marginBottom: 28, padding: 0, transition: 'color 0.15s',
        }}
        onMouseEnter={e => (e.currentTarget.style.color = '#E8EDF2')}
        onMouseLeave={e => (e.currentTarget.style.color = '#8B97A4')}
      >
        <ChevronLeft size={14} /> Back to History
      </button>

      {/* Attempt header */}
      {attempt?.problem && (
        <div style={{ marginBottom: 28 }}>
          <p style={{
            fontFamily: 'var(--font-mono)', fontSize: 10,
            color: '#56636F', marginBottom: 6,
          }}>
            {attempt.problem.title} · Attempt #{attempt.attempt_number}
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <h1 style={{
              fontSize: 22, fontWeight: 700, color: '#E8EDF2',
              letterSpacing: '-0.02em',
            }}>
              Evaluation Feedback
            </h1>
            <StatusBadge status={attempt.status} />
          </div>
        </div>
      )}

      {/* ── Evaluating ── */}
      {isEvaluating && (
        <div style={{
          border: '1px solid #1E252E', background: '#111519',
          padding: '48px 24px', textAlign: 'center',
        }}>
          <div style={{
            width: 48, height: 48, margin: '0 auto 16px',
            border: '1px solid rgba(14,165,160,0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <RefreshCw size={20} className="spin" style={{ color: '#0EA5A0' }} />
          </div>
          <h2 style={{ fontSize: 15, fontWeight: 600, color: '#E8EDF2', marginBottom: 8 }}>
            Evaluating Your Design
          </h2>
          <p style={{ fontSize: 12, color: '#8B97A4', maxWidth: 400, margin: '0 auto 20px', lineHeight: 1.7 }}>
            Analyzing class responsibilities, interfaces, abstractions, and trade-offs against 8 rubric criteria.
          </p>
          <Button variant="secondary" size="sm" icon={<RefreshCw size={12} />} onClick={loadData}>
            Refresh Status
          </Button>
        </div>
      )}

      {/* ── Failed ── */}
      {isFailed && (
        <div style={{
          border: '1px solid rgba(239,68,68,0.2)',
          background: 'rgba(239,68,68,0.03)',
          padding: '40px 24px', textAlign: 'center',
        }}>
          <AlertTriangle size={24} style={{ color: '#EF4444', margin: '0 auto 14px', display: 'block' }} />
          <h2 style={{ fontSize: 15, fontWeight: 600, color: '#E8EDF2', marginBottom: 6 }}>
            Evaluation could not complete
          </h2>
          <p style={{
            fontSize: 11, color: '#8B97A4', fontFamily: 'var(--font-mono)',
            maxWidth: 400, margin: '0 auto 8px', lineHeight: 1.7,
          }}>
            {evaluation?.error_message || 'An unexpected error occurred.'}
          </p>
          <p style={{ fontSize: 11, color: '#56636F', marginBottom: 20 }}>
            Your submission is preserved. You can trigger evaluation again.
          </p>
          <Button icon={<RotateCcw size={13} />} loading={retrying} onClick={handleRetry}>
            Retry Evaluation
          </Button>
        </div>
      )}

      {/* ── Completed ── */}
      {isCompleted && evaluation && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }} className="animate-fade-in">

          {/* Fallback notice */}
          {evaluation.is_fallback && (
            <div style={{
              border: '1px solid rgba(139,92,246,0.2)',
              background: 'rgba(139,92,246,0.05)',
              padding: '10px 14px',
              display: 'flex', gap: 8, alignItems: 'flex-start',
            }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#A78BFA', marginTop: 1 }}>
                FALLBACK
              </span>
              <p style={{ fontSize: 12, color: '#A78BFA' }}>
                Rule-based evaluation mode — AI evaluator was unavailable. Scores are based on structural analysis.
              </p>
            </div>
          )}

          {/* Score header */}
          <div style={{
            display: 'flex', alignItems: 'flex-start', gap: 24,
            borderBottom: '1px solid #1E252E', paddingBottom: 24,
            flexWrap: 'wrap',
          }}>
            <ScoreRing score={evaluation.overall_score || 0} size={80} />
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, flexWrap: 'wrap' }}>
                <span style={{
                  fontFamily: 'var(--font-mono)', fontSize: 32,
                  fontWeight: 700, color: '#E8EDF2', letterSpacing: '-0.03em',
                }}>
                  {Math.round(evaluation.overall_score || 0)}
                  <span style={{ fontSize: 14, color: '#56636F', fontWeight: 400 }}>/100</span>
                </span>
                <Badge
                  label={evaluation.is_fallback ? 'Rule-Based Engine' : 'AI Evaluator'}
                  variant={evaluation.is_fallback ? 'fallback' : 'ai'}
                />
              </div>
              <p style={{ fontSize: 13, color: '#8B97A4', lineHeight: 1.7, maxWidth: 480 }}>
                {evaluation.summary}
              </p>
            </div>
          </div>

          {/* Strengths & Improvements */}
          <div style={{ display: 'grid', gap: 16 }} className="sm:grid-cols-2">
            {/* Strengths */}
            <div style={{
              border: '1px solid rgba(34,197,94,0.15)',
              background: 'rgba(34,197,94,0.03)',
              padding: '16px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
                <CheckCircle2 size={13} style={{ color: '#22C55E' }} />
                <p className="label-mono" style={{ color: '#22C55E' }}>Strengths</p>
              </div>
              <ul style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {evaluation.strengths.map((st, i) => (
                  <li key={i} style={{
                    fontSize: 12, color: '#C5CDD6', lineHeight: 1.6,
                    display: 'flex', gap: 8, alignItems: 'flex-start',
                  }}>
                    <span style={{ color: '#22C55E', flexShrink: 0, marginTop: 2 }}>›</span>
                    {st}
                  </li>
                ))}
              </ul>
            </div>

            {/* Improvements */}
            <div style={{
              border: '1px solid rgba(245,158,11,0.15)',
              background: 'rgba(245,158,11,0.03)',
              padding: '16px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
                <Lightbulb size={13} style={{ color: '#F59E0B' }} />
                <p className="label-mono" style={{ color: '#F59E0B' }}>Improvements</p>
              </div>
              <ul style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {evaluation.improvements.map((imp, i) => (
                  <li key={i} style={{
                    fontSize: 12, color: '#C5CDD6', lineHeight: 1.6,
                    display: 'flex', gap: 8, alignItems: 'flex-start',
                  }}>
                    <span style={{ color: '#F59E0B', flexShrink: 0, marginTop: 2 }}>›</span>
                    {imp}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Criteria breakdown */}
          <div>
            <h2 style={{
              fontSize: 13, fontWeight: 600, color: '#E8EDF2', marginBottom: 12,
            }}>
              Criterion Breakdown
            </h2>
            <div style={{ borderTop: '1px solid #1E252E' }}>
              {evaluation.criteria.map((crit, idx) => (
                <CriterionRow key={idx} criterion={crit} index={idx} />
              ))}
            </div>
          </div>

          {/* Actions */}
          <div style={{
            paddingTop: 20, borderTop: '1px solid #1E252E',
            display: 'flex', gap: 10, flexWrap: 'wrap',
          }}>
            <Button size="md" icon={<RotateCcw size={13} />} onClick={handleTryAgain}>
              Try Again
            </Button>
            <Button size="md" variant="outline" icon={<ArrowRight size={13} />} onClick={() => navigate('/history')}>
              View History
            </Button>
          </div>
        </div>
      )}

      {/* Polling toast */}
      {polling && (
        <div style={{
          position: 'fixed', bottom: 16, right: 16,
          background: '#111519', border: '1px solid #1E252E',
          padding: '6px 12px', fontSize: 11, color: '#8B97A4',
          fontFamily: 'var(--font-mono)',
          display: 'flex', alignItems: 'center', gap: 6,
        }}>
          <RefreshCw size={11} className="spin" style={{ color: '#0EA5A0' }} />
          Checking status…
        </div>
      )}
    </PageLayout>
  );
}
