// Core domain types mirroring backend entities

export interface Problem {
  id: string;
  slug: string;
  title: string;
  difficulty: 'easy' | 'medium' | 'hard';
  short_description: string;
  detailed_requirements: string;
  assumptions: string;
  submission_guidance: string;
  created_at?: string;
}

export interface ClassEntry {
  name: string;
  responsibility: string;
  methods: string[];
  notes: string;
}

export interface Submission {
  id: string;
  attempt_id: string;
  submission_type: string;
  assumptions: string;
  classes: ClassEntry[];
  interfaces: string;
  relationships: string;
  design_explanation: string;
  edge_cases: string;
  submitted_at?: string;
}

export interface RubricCriterion {
  name: string;
  score: number;
  max_score: number;
  evidence: string;
  concern: string;
  suggestion: string;
  confidence: 'low' | 'medium' | 'high';
}

export interface Evaluation {
  id: string;
  attempt_id: string;
  status: 'pending' | 'evaluating' | 'completed' | 'failed';
  evaluator_type: string;
  overall_score: number | null;
  summary: string;
  strengths: string[];
  improvements: string[];
  criteria: RubricCriterion[];
  is_fallback: boolean;
  error_message: string | null;
  created_at?: string;
  completed_at?: string;
}

export interface Attempt {
  id: string;
  problem_id: string;
  learner_id: string;
  attempt_number: number;
  status: 'in_progress' | 'submitted' | 'evaluating' | 'completed' | 'failed';
  created_at?: string;
  updated_at?: string;
  problem?: Problem;
  submission?: Submission;
  evaluation?: Evaluation;
}

export interface ApiResponse<T> {
  status: 'ok' | 'error';
  message: string;
  data: T;
}

export interface SubmissionRequest {
  assumptions: string;
  classes: ClassEntry[];
  interfaces: string;
  relationships: string;
  design_explanation: string;
  edge_cases: string;
}
