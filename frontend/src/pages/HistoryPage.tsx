import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, TrendingDown, Minus, Eye, RotateCcw, ArrowRight, Clock, Trash2 } from 'lucide-react';
import { getAttempts, deleteAttempt, extractErrorMessage } from '../services/api';
import type { Attempt } from '../types';
import { DifficultyBadge, StatusBadge } from '../components/Badge';
import { Button } from '../components/Button';
import { PageLayout, LoadingSpinner, ErrorState, EmptyState, SectionTitle, ScoreRing } from '../components/UI';

interface GroupedAttempts {
  [problemId: string]: {
    problem: Attempt['problem'];
    attempts: Attempt[];
  };
}

export function HistoryPage() {
  const navigate = useNavigate();
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);

  const loadData = () => {
    setLoading(true);
    setError(null);
    getAttempts()
      .then(setAttempts)
      .catch(e => setError(extractErrorMessage(e)))
      .finally(() => setLoading(false));
  };

  useEffect(loadData, []);

  const handleDelete = async (attemptId: string) => {
    setDeletingId(attemptId);
    setConfirmingId(null);
    try {
      await deleteAttempt(attemptId);
      setAttempts(prev => prev.filter(a => a.id !== attemptId));
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setDeletingId(null);
    }
  };

  const grouped: GroupedAttempts = {};
  for (const a of attempts) {
    if (!a.problem_id) continue;
    if (!grouped[a.problem_id]) {
      grouped[a.problem_id] = { problem: a.problem, attempts: [] };
    }
    grouped[a.problem_id].attempts.push(a);
  }
  const groups = Object.values(grouped);

  return (
    <PageLayout>
      <SectionTitle
        title="Attempt History"
        subtitle={`${attempts.length} attempt${attempts.length !== 1 ? 's' : ''} across ${groups.length} problem${groups.length !== 1 ? 's' : ''}`}
      />

      {loading && <LoadingSpinner message="Fetching history…" />}
      {error && <ErrorState message={error} onRetry={loadData} />}

      {!loading && !error && attempts.length === 0 && (
        <EmptyState
          title="No attempts recorded"
          description="Start a Low-Level Design problem to begin tracking your design progress."
          icon={Clock}
          action={<Button onClick={() => navigate('/problems')}>Browse Problems</Button>}
        />
      )}

      {!loading && !error && groups.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 36 }}>
          {groups.map(({ problem, attempts: group }) => {
            const sortedGroup = [...group].sort((a, b) => a.attempt_number - b.attempt_number);
            const completedGroup = sortedGroup.filter(
              a => a.status === 'completed' && a.evaluation?.overall_score != null
            );
            const scores = completedGroup.map(a => a.evaluation!.overall_score!);
            const delta = scores.length >= 2 ? scores[scores.length - 1] - scores[0] : null;

            return (
              <div key={problem?.id}>
                {/* Problem group header */}
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  paddingBottom: 10, borderBottom: '1px solid #2A3340',
                  marginBottom: 0, flexWrap: 'wrap',
                }}>
                  <h2 style={{ fontSize: 14, fontWeight: 600, color: '#E8EDF2' }}>
                    {problem?.title}
                  </h2>
                  {problem && <DifficultyBadge difficulty={problem.difficulty} />}

                  {delta !== null && (
                    <span style={{
                      fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600,
                      padding: '2px 7px',
                      background: delta > 0
                        ? 'rgba(34,197,94,0.08)'
                        : delta < 0
                        ? 'rgba(239,68,68,0.08)'
                        : '#171B21',
                      color: delta > 0 ? '#4ADE80' : delta < 0 ? '#F87171' : '#8B97A4',
                      border: `1px solid ${delta > 0 ? 'rgba(34,197,94,0.2)' : delta < 0 ? 'rgba(239,68,68,0.2)' : '#1E252E'}`,
                      display: 'inline-flex', alignItems: 'center', gap: 4,
                      marginLeft: 'auto',
                    }}>
                      {delta > 0 ? <TrendingUp size={11} /> : delta < 0 ? <TrendingDown size={11} /> : <Minus size={11} />}
                      {delta > 0 ? '+' : ''}{Math.round(delta)} pts
                    </span>
                  )}
                </div>

                {/* Attempt rows */}
                <div>
                  {sortedGroup.map(attempt => (
                    <div
                      key={attempt.id}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 16,
                        padding: '11px 0', borderBottom: '1px solid #1E252E',
                        flexWrap: 'wrap',
                      }}
                    >
                      {/* Attempt number */}
                      <span style={{
                        fontFamily: 'var(--font-mono)', fontSize: 11,
                        color: '#56636F', minWidth: 28,
                        flexShrink: 0,
                      }}>
                        #{attempt.attempt_number}
                      </span>

                      {/* Status & date */}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                          <StatusBadge status={attempt.status} />
                          {attempt.evaluation?.is_fallback && (
                            <span style={{
                              fontFamily: 'var(--font-mono)', fontSize: 9,
                              color: '#A78BFA',
                              background: 'rgba(139,92,246,0.08)',
                              border: '1px solid rgba(139,92,246,0.2)',
                              padding: '1px 5px',
                            }}>
                              RULE-BASED
                            </span>
                          )}
                        </div>
                        <p style={{
                          fontFamily: 'var(--font-mono)', fontSize: 10,
                          color: '#56636F', marginTop: 3,
                        }}>
                          {attempt.created_at
                            ? new Date(attempt.created_at).toLocaleString('en-US', {
                                month: 'short', day: 'numeric', year: 'numeric',
                                hour: '2-digit', minute: '2-digit',
                              })
                            : 'Recent'}
                        </p>
                      </div>

                      {/* Score */}
                      <div style={{ flexShrink: 0 }}>
                        {attempt.evaluation?.overall_score != null ? (
                          <ScoreRing score={attempt.evaluation.overall_score} size={38} />
                        ) : (
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#56636F' }}>—</span>
                        )}
                      </div>

                      {/* Actions */}
                      <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexShrink: 0 }}>
                        {attempt.status === 'completed' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            icon={<Eye size={12} />}
                            onClick={() => navigate(`/attempt/${attempt.id}/feedback`)}
                          >
                            Review
                          </Button>
                        )}
                        {attempt.status === 'in_progress' && (
                          <Button
                            variant="outline"
                            size="sm"
                            icon={<ArrowRight size={12} />}
                            onClick={() => navigate(`/attempt/${attempt.id}`)}
                          >
                            Continue
                          </Button>
                        )}
                        {(attempt.status === 'completed' || attempt.status === 'failed') && problem && (
                          <Button
                            variant="secondary"
                            size="sm"
                            icon={<RotateCcw size={11} />}
                            onClick={() => navigate(`/problems/${problem.id}`)}
                          >
                            Retry
                          </Button>
                        )}
                        {confirmingId === attempt.id ? (
                          <div style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}>
                            <Button
                              variant="danger"
                              size="sm"
                              loading={deletingId === attempt.id}
                              onClick={() => handleDelete(attempt.id)}
                            >
                              Confirm
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setConfirmingId(null)}
                            >
                              Cancel
                            </Button>
                          </div>
                        ) : (
                          <Button
                            variant="ghost"
                            size="sm"
                            icon={<Trash2 size={12} />}
                            onClick={() => setConfirmingId(attempt.id)}
                            title="Delete attempt"
                          >
                            Delete
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </PageLayout>
  );
}
