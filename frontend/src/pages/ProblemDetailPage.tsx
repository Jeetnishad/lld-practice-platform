import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft, ArrowRight, PlayCircle } from 'lucide-react';
import { getProblem, createAttempt, getAttempts, extractErrorMessage } from '../services/api';
import type { Problem, Attempt } from '../types';
import { DifficultyBadge, StatusBadge } from '../components/Badge';
import { Button } from '../components/Button';
import { PageLayout, LoadingSpinner, ErrorState } from '../components/UI';

export function ProblemDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [problem, setProblem] = useState<Problem | null>(null);
  const [existingAttempts, setExistingAttempts] = useState<Attempt[]>([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    Promise.all([getProblem(id), getAttempts().catch(() => [])])
      .then(([p, attempts]) => {
        setProblem(p);
        setExistingAttempts(attempts.filter(a => a.problem_id === p.id));
      })
      .catch(e => setError(extractErrorMessage(e)))
      .finally(() => setLoading(false));
  }, [id]);

  const activeAttempt = existingAttempts.find(
    a => a.status === 'in_progress' || a.status === 'evaluating'
  );

  const handleStartAttempt = async () => {
    if (!problem) return;
    if (activeAttempt) {
      navigate(
        activeAttempt.status === 'evaluating'
          ? `/attempt/${activeAttempt.id}/feedback`
          : `/attempt/${activeAttempt.id}`
      );
      return;
    }
    setStarting(true);
    try {
      const attempt = await createAttempt(problem.id);
      navigate(`/attempt/${attempt.id}`);
    } catch (e) {
      setError(extractErrorMessage(e));
      setStarting(false);
    }
  };

  if (loading) return <PageLayout><LoadingSpinner message="Loading problem…" /></PageLayout>;
  if (error || !problem) return (
    <PageLayout>
      <ErrorState message={error || 'Problem not found'} onRetry={() => navigate('/problems')} />
    </PageLayout>
  );

  const requirementLines = problem.detailed_requirements
    .split('\n').map(l => l.trim()).filter(Boolean);

  return (
    <PageLayout maxWidth="4xl">
      {/* Back */}
      <button
        onClick={() => navigate('/problems')}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 4,
          color: '#8B97A4', fontSize: 12, background: 'none', border: 'none',
          cursor: 'pointer', marginBottom: 28, padding: 0,
          transition: 'color 0.15s',
        }}
        onMouseEnter={e => (e.currentTarget.style.color = '#E8EDF2')}
        onMouseLeave={e => (e.currentTarget.style.color = '#8B97A4')}
      >
        <ChevronLeft size={14} /> Back to Problems
      </button>

      {/* ── Problem header ── */}
      <div style={{ marginBottom: 36 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
          <DifficultyBadge difficulty={problem.difficulty} />
          {existingAttempts.length > 0 && (
            <span style={{
              fontFamily: 'var(--font-mono)', fontSize: 9, color: '#8B97A4',
              background: '#171B21', border: '1px solid #1E252E', padding: '1px 7px',
            }}>
              {existingAttempts.length} attempt{existingAttempts.length !== 1 ? 's' : ''} on record
            </span>
          )}
        </div>

        <h1 style={{
          fontSize: 24, fontWeight: 700, color: '#E8EDF2',
          letterSpacing: '-0.02em', lineHeight: 1.2, marginBottom: 10,
        }}>
          {problem.title}
        </h1>
        <p style={{ fontSize: 13, color: '#8B97A4', lineHeight: 1.7, maxWidth: 580, marginBottom: 20 }}>
          {problem.short_description}
        </p>

        {/* CTA */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <Button
            size="md"
            loading={starting}
            icon={activeAttempt ? <PlayCircle size={14} /> : <ArrowRight size={14} />}
            onClick={handleStartAttempt}
          >
            {activeAttempt ? 'Resume Attempt' : 'Start Practice'}
          </Button>
          {activeAttempt && (
            <StatusBadge status={activeAttempt.status} />
          )}
        </div>
      </div>

      {/* ── Divider ── */}
      <hr style={{ border: 'none', borderTop: '1px solid #1E252E', marginBottom: 32 }} />

      {/* ── Active attempt notice ── */}
      {activeAttempt && (
        <div style={{
          border: '1px solid rgba(245,158,11,0.2)',
          background: 'rgba(245,158,11,0.04)',
          padding: '10px 16px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          gap: 12, flexWrap: 'wrap', marginBottom: 28,
        }}>
          <p style={{ fontSize: 12, color: '#FBB83F' }}>
            Active attempt #{activeAttempt.attempt_number} in progress
          </p>
          <Button size="sm" variant="outline" onClick={() => navigate(`/attempt/${activeAttempt.id}`)}>
            Continue
          </Button>
        </div>
      )}

      {/* ── Spec sections ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>

        {/* 1. Requirements */}
        <section>
          <div style={{ borderLeft: '2px solid #0EA5A0', paddingLeft: 14, marginBottom: 16 }}>
            <p className="label-mono" style={{ color: '#0EA5A0', marginBottom: 2 }}>01 — Requirements</p>
            <h2 style={{ fontSize: 15, fontWeight: 600, color: '#E8EDF2' }}>Functional Requirements</h2>
            <p style={{ fontSize: 12, color: '#8B97A4', marginTop: 2 }}>
              Core functionality your class design must satisfy
            </p>
          </div>
          <div style={{ paddingLeft: 26 }}>
            {requirementLines.map((req, idx) => (
              <div key={idx} style={{
                display: 'flex', gap: 12,
                padding: '8px 0', borderBottom: '1px solid #1E252E',
              }}>
                <span style={{
                  fontFamily: 'var(--font-mono)', fontSize: 10,
                  color: '#0EA5A0', minWidth: 20, paddingTop: 1,
                }}>
                  {idx + 1}.
                </span>
                <span style={{ fontSize: 13, color: '#C5CDD6', lineHeight: 1.6 }}>
                  {req.replace(/^\d+[\.)]\s*/, '')}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* 2. Constraints */}
        <section>
          <div style={{ borderLeft: '2px solid #0EA5A0', paddingLeft: 14, marginBottom: 16 }}>
            <p className="label-mono" style={{ color: '#0EA5A0', marginBottom: 2 }}>02 — Constraints</p>
            <h2 style={{ fontSize: 15, fontWeight: 600, color: '#E8EDF2' }}>Assumptions & System Constraints</h2>
            <p style={{ fontSize: 12, color: '#8B97A4', marginTop: 2 }}>
              Default boundaries to design within
            </p>
          </div>
          <div style={{
            background: '#0C0F13', border: '1px solid #1E252E',
            padding: '14px 16px', marginLeft: 26,
          }}>
            <pre style={{
              fontFamily: 'var(--font-mono)', fontSize: 11.5,
              color: '#8B97A4', whiteSpace: 'pre-wrap', lineHeight: 1.75,
              margin: 0,
            }}>
              {problem.assumptions}
            </pre>
          </div>
        </section>

        {/* 3. Expected deliverables */}
        <section>
          <div style={{ borderLeft: '2px solid #0EA5A0', paddingLeft: 14, marginBottom: 16 }}>
            <p className="label-mono" style={{ color: '#0EA5A0', marginBottom: 2 }}>03 — Deliverables</p>
            <h2 style={{ fontSize: 15, fontWeight: 600, color: '#E8EDF2' }}>Expected Submission</h2>
            <p style={{ fontSize: 12, color: '#8B97A4', marginTop: 2 }}>
              What your structured solution should cover
            </p>
          </div>
          <div style={{
            display: 'grid', gap: 1,
            background: '#1E252E', marginLeft: 26,
          }}
            className="sm:grid-cols-2">
            {[
              ['Class Architecture',        'Core entities with single responsibility definitions'],
              ['Interfaces & Abstractions', 'Contracts where behavior may vary'],
              ['Object Relationships',      'Inheritance, Composition, Dependency Injection'],
              ['Design Trade-offs',         'Pattern selection, architectural reasoning, edge cases'],
            ].map(([head, desc]) => (
              <div key={head} style={{ background: '#111519', padding: '12px 16px' }}>
                <p style={{ fontSize: 11, fontWeight: 600, color: '#2DD4BF', marginBottom: 4 }}>{head}</p>
                <p style={{ fontSize: 11, color: '#8B97A4', lineHeight: 1.5 }}>{desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* 4. Rubric */}
        <section>
          <div style={{ borderLeft: '2px solid #0EA5A0', paddingLeft: 14, marginBottom: 16 }}>
            <p className="label-mono" style={{ color: '#0EA5A0', marginBottom: 2 }}>04 — Rubric</p>
            <h2 style={{ fontSize: 15, fontWeight: 600, color: '#E8EDF2' }}>Evaluation Criteria</h2>
            <p style={{ fontSize: 12, color: '#8B97A4', marginTop: 2 }}>
              8 criteria scored 0–10 each (100 points total)
            </p>
          </div>
          <div style={{
            borderTop: '1px solid #1E252E', marginLeft: 26,
          }}>
            {[
              '1. Requirement Understanding',
              '2. Class Responsibilities',
              '3. Encapsulation & Interfaces',
              '4. Coupling & Cohesion',
              '5. Abstraction / Patterns',
              '6. Extensibility',
              '7. Edge Cases & Testability',
              '8. Design Explanation',
            ].map((crit, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '9px 0', borderBottom: '1px solid #1E252E',
              }}>
                <span style={{ fontSize: 12, color: '#C5CDD6' }}>{crit}</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: '#56636F' }}>
                  10 pts
                </span>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* ── Bottom CTA ── */}
      <div style={{
        marginTop: 40, paddingTop: 28,
        borderTop: '1px solid #1E252E',
        display: 'flex', justifyContent: 'center',
      }}>
        <Button size="lg" loading={starting} icon={<ArrowRight size={15} />} onClick={handleStartAttempt}>
          {activeAttempt ? 'Resume Active Attempt' : 'Start Practice Attempt'}
        </Button>
      </div>
    </PageLayout>
  );
}
