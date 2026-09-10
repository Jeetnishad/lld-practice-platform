import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Plus, Trash2, ChevronLeft, Send, CheckCircle2, AlertCircle } from 'lucide-react';
import { getAttempt, submitSolution, extractErrorMessage } from '../services/api';
import type { Attempt, ClassEntry } from '../types';
import { Button } from '../components/Button';
import { DifficultyBadge } from '../components/Badge';
import { LoadingSpinner, ErrorState, Input, Textarea, FormSection } from '../components/UI';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function newClass(): ClassEntry {
  return { name: '', responsibility: '', methods: [], notes: '' };
}

// ---------------------------------------------------------------------------
// Class Card
// ---------------------------------------------------------------------------

function ClassCard({
  cls,
  index,
  errors,
  onChange,
  onRemove,
}: {
  cls: ClassEntry;
  index: number;
  errors?: { name?: string; responsibility?: string };
  onChange: (updated: ClassEntry) => void;
  onRemove: () => void;
}) {
  const methodsStr = cls.methods.join('\n');

  return (
    <div className="animate-fade-in" style={{
      background: '#0C0F13', border: '1px solid #1E252E',
      padding: '16px', marginBottom: 12,
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 14, paddingBottom: 10, borderBottom: '1px solid #1E252E',
      }}>
        <span style={{
          fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600,
          color: '#0EA5A0', letterSpacing: '0.08em', textTransform: 'uppercase',
        }}>
          Class #{index + 1}
        </span>
        <button
          type="button"
          onClick={onRemove}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: '#56636F', padding: '2px 4px', transition: 'color 0.15s',
          }}
          onMouseEnter={e => (e.currentTarget.style.color = '#EF4444')}
          onMouseLeave={e => (e.currentTarget.style.color = '#56636F')}
          title="Remove class"
        >
          <Trash2 size={13} />
        </button>
      </div>

      <div style={{ display: 'grid', gap: 12, gridTemplateColumns: '1fr 1fr' }}
        className="sm:grid-cols-2">
        <Input
          id={`class-name-${index}`}
          label="Class Name"
          required
          value={cls.name}
          onChange={e => onChange({ ...cls, name: e.target.value })}
          placeholder="e.g. ParkingLot"
          error={errors?.name}
          helperText="Unique entity identifier"
        />
        <Input
          id={`class-notes-${index}`}
          label="Notes / Annotations"
          value={cls.notes}
          onChange={e => onChange({ ...cls, notes: e.target.value })}
          placeholder="e.g. Implements PaymentProcessor"
          helperText="Pattern role or detail"
        />
      </div>

      <div style={{ marginTop: 12 }}>
        <Textarea
          id={`class-resp-${index}`}
          label="Single Responsibility Statement"
          required
          value={cls.responsibility}
          onChange={e => onChange({ ...cls, responsibility: e.target.value })}
          placeholder="What is this class's single, primary responsibility?"
          rows={2}
          error={errors?.responsibility}
          helperText="1–2 sentences defining its sole purpose"
        />
      </div>

      <div style={{ marginTop: 12 }}>
        <Textarea
          id={`class-methods-${index}`}
          label="Core Public Methods (one per line)"
          value={methodsStr}
          onChange={e =>
            onChange({
              ...cls,
              methods: e.target.value.split('\n').map(m => m.trim()).filter(Boolean),
            })
          }
          placeholder={`enterVehicle(vehicle: Vehicle): Ticket\nexitVehicle(ticketId: string): Receipt`}
          rows={3}
          helperText="Method signatures and return types"
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main WorkspacePage
// ---------------------------------------------------------------------------

export function WorkspacePage() {
  const { id: attemptId } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Form fields
  const [assumptions, setAssumptions]               = useState('');
  const [classes, setClasses]                       = useState<ClassEntry[]>([newClass()]);
  const [interfaces, setInterfaces]                 = useState('');
  const [relationships, setRelationships]           = useState('');
  const [designExplanation, setDesignExplanation]   = useState('');
  const [edgeCases, setEdgeCases]                   = useState('');

  // Validation
  const [classErrors, setClassErrors] = useState<Record<number, { name?: string; responsibility?: string }>>({});
  const [formErrors, setFormErrors]   = useState<{ classes?: string; designExplanation?: string }>({});

  useEffect(() => {
    if (!attemptId) return;
    setLoading(true);
    getAttempt(attemptId)
      .then(a => {
        setAttempt(a);
        if (a.status === 'completed' || a.status === 'evaluating') {
          navigate(`/attempt/${attemptId}/feedback`, { replace: true });
        }
        if (a.submission) {
          setAssumptions(a.submission.assumptions || '');
          setClasses(a.submission.classes.length > 0 ? a.submission.classes : [newClass()]);
          setInterfaces(a.submission.interfaces || '');
          setRelationships(a.submission.relationships || '');
          setDesignExplanation(a.submission.design_explanation || '');
          setEdgeCases(a.submission.edge_cases || '');
        }
      })
      .catch(e => setLoadError(extractErrorMessage(e)))
      .finally(() => setLoading(false));
  }, [attemptId, navigate]);

  const addClass   = () => setClasses(prev => [...prev, newClass()]);
  const removeClass = (index: number) =>
    setClasses(prev => prev.length > 1 ? prev.filter((_, i) => i !== index) : prev);
  const updateClass = (index: number, updated: ClassEntry) =>
    setClasses(prev => prev.map((c, i) => (i === index ? updated : c)));

  const validateForm = useCallback((): boolean => {
    const newClassErrs: Record<number, { name?: string; responsibility?: string }> = {};
    const newFormErrs: { classes?: string; designExplanation?: string } = {};

    const hasValidClass = classes.some(c => c.name.trim().length > 0);
    if (!hasValidClass) {
      newFormErrs.classes = 'At least one class with a valid class name is required.';
    }
    if (!designExplanation.trim()) {
      newFormErrs.designExplanation = 'Design explanation is required.';
    }
    classes.forEach((cls, idx) => {
      if (cls.name.trim() && !cls.responsibility.trim()) {
        newClassErrs[idx] = { ...(newClassErrs[idx] || {}), responsibility: 'Responsibility statement is required.' };
      }
    });

    setClassErrors(newClassErrs);
    setFormErrors(newFormErrs);
    return Object.keys(newFormErrs).length === 0 && Object.keys(newClassErrs).length === 0;
  }, [classes, designExplanation]);

  const handleSubmit = async () => {
    if (!validateForm()) {
      document.querySelector('[style*="border-color: rgb(239"]')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      return;
    }
    setSubmitting(true);
    setSubmitError(null);
    try {
      await submitSolution(attemptId!, {
        assumptions,
        classes: classes.filter(c => c.name.trim()),
        interfaces,
        relationships,
        design_explanation: designExplanation,
        edge_cases: edgeCases,
      });
      navigate(`/attempt/${attemptId}/feedback`);
    } catch (e) {
      setSubmitError(extractErrorMessage(e));
      setSubmitting(false);
    }
  };

  const scrollToSection = (id: string) =>
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });

  if (loading) {
    return (
      <div style={{ paddingTop: 80 }}>
        <LoadingSpinner message="Opening workspace…" />
      </div>
    );
  }
  if (loadError || !attempt) {
    return (
      <div style={{ paddingTop: 80 }}>
        <ErrorState message={loadError || 'Attempt not found'} onRetry={() => navigate('/problems')} />
      </div>
    );
  }

  const problem = attempt.problem;

  return (
    <div style={{ minHeight: '100vh', background: '#0C0F13', color: '#E8EDF2' }}>

      {/* ── Sticky workspace header ── */}
      <header style={{
        position: 'fixed', top: 48, left: 0, right: 0, zIndex: 40,
        background: '#0C0F13', borderBottom: '1px solid #1E252E',
      }}>
        {/* Main bar */}
        <div style={{
          maxWidth: 1200, margin: '0 auto', padding: '0 20px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          gap: 12, height: 44,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
            <button
              onClick={() => navigate(`/problems/${problem?.id}`)}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: '#8B97A4', padding: '2px',
                display: 'flex', transition: 'color 0.15s',
              }}
              onMouseEnter={e => (e.currentTarget.style.color = '#E8EDF2')}
              onMouseLeave={e => (e.currentTarget.style.color = '#8B97A4')}
              title="Back to problem"
            >
              <ChevronLeft size={16} />
            </button>
            <div style={{ minWidth: 0 }}>
              <h1 style={{
                fontSize: 13, fontWeight: 600, color: '#E8EDF2',
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {problem?.title}
              </h1>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 1 }}>
                {problem && <DifficultyBadge difficulty={problem.difficulty} />}
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: '#56636F' }}>
                  Attempt #{attempt.attempt_number}
                </span>
              </div>
            </div>
          </div>

          <Button
            id="submit-solution-btn-top"
            size="sm"
            loading={submitting}
            disabled={submitting}
            icon={<Send size={12} />}
            onClick={handleSubmit}
          >
            {submitting ? 'Submitting…' : 'Submit Solution'}
          </Button>
        </div>

        {/* Section quick-jump */}
        <div style={{
          maxWidth: 1200, margin: '0 auto', padding: '0 20px',
          borderTop: '1px solid #1E252E',
          display: 'flex', gap: 0, overflowX: 'auto',
        }} className="no-scrollbar">
          {[
            ['sec-assumptions',  '1. Assumptions'],
            ['sec-classes',      '2. Classes'],
            ['sec-interfaces',   '3. Interfaces'],
            ['sec-relationships','4. Relationships'],
            ['sec-explanation',  '5. Rationale'],
            ['sec-edge-cases',   '6. Edge Cases'],
          ].map(([secId, label]) => (
            <button
              key={secId}
              onClick={() => scrollToSection(secId)}
              style={{
                fontFamily: 'var(--font-mono)', fontSize: 10,
                color: '#56636F', padding: '6px 12px',
                background: 'none', border: 'none', borderRight: '1px solid #1E252E',
                cursor: 'pointer', whiteSpace: 'nowrap', transition: 'color 0.15s',
                letterSpacing: '0.04em',
              }}
              onMouseEnter={e => (e.currentTarget.style.color = '#2DD4BF')}
              onMouseLeave={e => (e.currentTarget.style.color = '#56636F')}
            >
              {label}
            </button>
          ))}
        </div>
      </header>

      {/* ── Workspace body ── */}
      <div style={{
        maxWidth: 1200, margin: '0 auto',
        padding: '108px 20px 80px',
        display: 'grid', gap: 24,
      }} className="lg:grid-cols-5">

        {/* ── Left: Problem reference ── */}
        <div style={{ gridColumn: 'span 2 / span 2' }} className="lg:col-span-2">
          <div style={{
            position: 'sticky', top: 108,
            background: '#111519', border: '1px solid #1E252E',
            padding: '16px',
          }}>
            <p className="label-mono" style={{ color: '#0EA5A0', marginBottom: 12 }}>
              Problem Reference
            </p>
            <div style={{
              maxHeight: '70vh', overflowY: 'auto',
              fontSize: 11.5, color: '#8B97A4', lineHeight: 1.7,
            }} className="no-scrollbar">
              <p style={{ fontWeight: 600, color: '#C5CDD6', marginBottom: 6 }}>Requirements</p>
              <p style={{ whiteSpace: 'pre-wrap', marginBottom: 20 }}>{problem?.detailed_requirements}</p>
              <hr style={{ border: 'none', borderTop: '1px solid #1E252E', marginBottom: 14 }} />
              <p style={{ fontWeight: 600, color: '#C5CDD6', marginBottom: 6 }}>Constraints & Guidance</p>
              <p style={{ whiteSpace: 'pre-wrap' }}>{problem?.submission_guidance}</p>
            </div>
          </div>
        </div>

        {/* ── Right: Design form ── */}
        <div style={{ gridColumn: 'span 3 / span 3' }} className="lg:col-span-3">

          {/* Submit error */}
          {submitError && (
            <div className="animate-fade-in" style={{
              border: '1px solid rgba(239,68,68,0.3)',
              background: 'rgba(239,68,68,0.05)',
              padding: '10px 14px',
              display: 'flex', alignItems: 'flex-start', gap: 8,
              color: '#F87171', fontSize: 12, marginBottom: 16,
            }}>
              <AlertCircle size={14} style={{ marginTop: 1, flexShrink: 0 }} />
              <div>
                <p style={{ fontWeight: 600 }}>Submission Error</p>
                <p style={{ marginTop: 2, color: '#8B97A4' }}>{submitError}</p>
              </div>
            </div>
          )}

          {/* 1. Assumptions */}
          <FormSection
            id="sec-assumptions"
            title="1. Assumptions & Constraints"
            purpose="State the scale, constraints, and operational assumptions you are making."
          >
            <Textarea
              id="assumptions"
              value={assumptions}
              onChange={e => setAssumptions(e.target.value)}
              placeholder="e.g. Single parking lot with multi-floor capacity. Nearest-spot assignment. Flat hourly rate."
              rows={3}
            />
          </FormSection>

          {/* 2. Classes */}
          <FormSection
            id="sec-classes"
            title="2. Class Architecture"
            purpose="Define core objects, single-responsibility contracts, methods."
            required
            action={
              <Button type="button" variant="outline" size="sm" icon={<Plus size={12} />} onClick={addClass}>
                Add Class
              </Button>
            }
          >
            {formErrors.classes && (
              <p style={{
                fontSize: 11, color: '#EF4444', marginBottom: 10,
                display: 'flex', alignItems: 'center', gap: 4,
              }}>
                <AlertCircle size={11} /> {formErrors.classes}
              </p>
            )}
            {classes.map((cls, i) => (
              <ClassCard
                key={i}
                cls={cls}
                index={i}
                errors={classErrors[i]}
                onChange={updated => updateClass(i, updated)}
                onRemove={() => removeClass(i)}
              />
            ))}
          </FormSection>

          {/* 3. Interfaces */}
          <FormSection
            id="sec-interfaces"
            title="3. Interfaces & Abstract Classes"
            purpose="Identify abstractions where behavior may vary or strategy patterns apply."
          >
            <Textarea
              id="interfaces"
              value={interfaces}
              onChange={e => setInterfaces(e.target.value)}
              placeholder={`e.g. PaymentProcessor: processPayment(amount: number) -> Receipt\nSpotAssignmentStrategy: findSpot(vehicle: Vehicle) -> ParkingSpot`}
              rows={4}
            />
          </FormSection>

          {/* 4. Relationships */}
          <FormSection
            id="sec-relationships"
            title="4. Object Relationships & Collaborations"
            purpose="Explain how objects collaborate (Inheritance, Composition, Dependency Injection)."
          >
            <Textarea
              id="relationships"
              value={relationships}
              onChange={e => setRelationships(e.target.value)}
              placeholder={`e.g. ParkingLot has-many ParkingFloor\nParkingFloor has-many ParkingSpot\nSpotAssignmentStrategy is injected into EntryHandler`}
              rows={4}
            />
          </FormSection>

          {/* 5. Design Explanation */}
          <FormSection
            id="sec-explanation"
            title="5. Design Rationale & Trade-offs"
            purpose="Explain architectural decisions, patterns used, and trade-offs."
            required
          >
            <Textarea
              id="design-explanation"
              required
              value={designExplanation}
              onChange={e => setDesignExplanation(e.target.value)}
              error={formErrors.designExplanation}
              placeholder={`1. Why did you choose these class boundaries?\n2. What design patterns did you apply?\n3. What trade-offs did you accept?`}
              rows={6}
            />
          </FormSection>

          {/* 6. Edge Cases */}
          <FormSection
            id="sec-edge-cases"
            title="6. Edge Cases & Error Modes"
            purpose="Identify boundary conditions, failure modes, and concurrency issues."
          >
            <Textarea
              id="edge-cases"
              value={edgeCases}
              onChange={e => setEdgeCases(e.target.value)}
              placeholder={`e.g. Lot full: reject with LotFullException\nConcurrent entry: floor-level locking\nInvalid ticket: log and reject exit`}
              rows={4}
            />
          </FormSection>

          {/* Bottom submit */}
          <div style={{
            marginTop: 32, paddingTop: 20,
            borderTop: '1px solid #1E252E',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            gap: 12, flexWrap: 'wrap',
          }}>
            <span style={{
              fontSize: 11, color: '#56636F',
              display: 'flex', alignItems: 'center', gap: 5,
            }}>
              <CheckCircle2 size={12} style={{ color: '#22C55E' }} />
              Submission saved on server
            </span>
            <Button
              id="submit-solution-btn-bottom"
              size="md"
              loading={submitting}
              disabled={submitting}
              icon={<Send size={13} />}
              onClick={handleSubmit}
            >
              {submitting ? 'Submitting…' : 'Submit Solution'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
