import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProblems, getAttempts, extractErrorMessage } from '../services/api';
import type { Problem, Attempt } from '../types';
import { DifficultyBadge } from '../components/Badge';
import { Button } from '../components/Button';
import { PageLayout, LoadingSpinner, ErrorState, SectionTitle, Input } from '../components/UI';
import { ArrowRight, Search, Clock } from 'lucide-react';

const ESTIMATED_TIMES: Record<string, string> = {
  'parking-lot':         '30–45 min',
  'elevator-system':     '45–60 min',
  'vending-machine':     '30–40 min',
  'movie-ticket-booking':'45–60 min',
  'splitwise':           '40–50 min',
};

export function ProblemsPage() {
  const navigate = useNavigate();
  const [problems, setProblems] = useState<Problem[]>([]);
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('all');

  const loadData = () => {
    setLoading(true);
    setError(null);
    Promise.all([getProblems(), getAttempts().catch(() => [])])
      .then(([pList, aList]) => { setProblems(pList); setAttempts(aList); })
      .catch(e => setError(extractErrorMessage(e)))
      .finally(() => setLoading(false));
  };

  useEffect(loadData, []);

  const attemptCounts: Record<string, number> = {};
  for (const a of attempts) {
    if (a.problem_id) {
      attemptCounts[a.problem_id] = (attemptCounts[a.problem_id] || 0) + 1;
    }
  }

  const filteredProblems = problems.filter(p => {
    const matchesSearch =
      p.title.toLowerCase().includes(search.toLowerCase()) ||
      p.short_description.toLowerCase().includes(search.toLowerCase());
    const matchesDiff = difficultyFilter === 'all' || p.difficulty.toLowerCase() === difficultyFilter;
    return matchesSearch && matchesDiff;
  });

  return (
    <PageLayout>
      <SectionTitle
        title="Practice Problems"
        subtitle="Choose a problem, model the class architecture, and receive evaluator feedback."
      />

      {/* Filter bar */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12,
        marginBottom: 28, flexWrap: 'wrap',
      }}>
        {/* Search */}
        <div style={{ position: 'relative', width: 240 }}>
          <Input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search problems…"
            style={{ paddingLeft: 32 }}
          />
          <Search size={13} style={{
            position: 'absolute', left: 10, top: '50%',
            transform: 'translateY(-50%)', color: '#56636F', pointerEvents: 'none',
          }} />
        </div>

        {/* Difficulty filter */}
        <div style={{ display: 'flex', gap: 2 }}>
          {['all', 'easy', 'medium', 'hard'].map(diff => (
            <button
              key={diff}
              onClick={() => setDifficultyFilter(diff)}
              style={{
                padding: '4px 10px', fontSize: 10,
                fontFamily: 'var(--font-mono)', fontWeight: 600,
                textTransform: 'uppercase', letterSpacing: '0.07em',
                background: difficultyFilter === diff ? '#0EA5A0' : '#111519',
                color: difficultyFilter === diff ? '#0C0F13' : '#8B97A4',
                border: `1px solid ${difficultyFilter === diff ? '#0EA5A0' : '#1E252E'}`,
                cursor: 'pointer', transition: 'all 0.15s',
              }}
            >
              {diff}
            </button>
          ))}
        </div>
      </div>

      {loading && <LoadingSpinner message="Loading problems…" />}
      {error && <ErrorState message={error} onRetry={loadData} />}

      {!loading && !error && (
        <div style={{ borderTop: '1px solid #1E252E' }}>
          {filteredProblems.map((problem, idx) => {
            const count = attemptCounts[problem.id] || 0;
            const estTime = ESTIMATED_TIMES[problem.slug] || '30–45 min';

            return (
              <div
                key={problem.id}
                onClick={() => navigate(`/problems/${problem.id}`)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 20,
                  padding: '16px 0', borderBottom: '1px solid #1E252E',
                  cursor: 'pointer', transition: 'background 0.12s, padding 0.12s',
                }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLElement).style.background = '#111519';
                  (e.currentTarget as HTMLElement).style.paddingLeft = '12px';
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLElement).style.background = 'transparent';
                  (e.currentTarget as HTMLElement).style.paddingLeft = '0px';
                }}
              >
                {/* Index number */}
                <span style={{
                  fontFamily: 'var(--font-mono)', fontSize: 11,
                  color: '#56636F', minWidth: 24, flexShrink: 0,
                }}>
                  {String(idx + 1).padStart(2, '0')}
                </span>

                {/* Main content */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, flexWrap: 'wrap' }}>
                    <h3 style={{ fontSize: 14, fontWeight: 600, color: '#E8EDF2' }}>
                      {problem.title}
                    </h3>
                    <DifficultyBadge difficulty={problem.difficulty} />
                    {count > 0 && (
                      <span style={{
                        fontFamily: 'var(--font-mono)', fontSize: 9,
                        color: '#0EA5A0', background: 'rgba(14,165,160,0.1)',
                        border: '1px solid rgba(14,165,160,0.2)', padding: '1px 6px',
                      }}>
                        {count} attempt{count !== 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                  <p style={{ fontSize: 12, color: '#8B97A4', lineHeight: 1.5 }}>
                    {problem.short_description}
                  </p>
                </div>

                {/* Time estimate + CTA */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexShrink: 0 }}>
                  <span style={{
                    fontFamily: 'var(--font-mono)', fontSize: 10, color: '#56636F',
                    display: 'flex', alignItems: 'center', gap: 4,
                  }}>
                    <Clock size={11} /> {estTime}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    icon={<ArrowRight size={12} />}
                    onClick={e => { e.stopPropagation(); navigate(`/problems/${problem.id}`); }}
                  >
                    View
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </PageLayout>
  );
}
