/**
 * API service layer — all backend calls go through here.
 * Uses the Vite proxy (/api → http://localhost:5000/api) in dev.
 * Uses VITE_API_URL environment variable in production.
 */
import axios from 'axios';
import type { ApiResponse, Attempt, Evaluation, Problem, SubmissionRequest } from '../types';

const BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
});

// ---------------------------------------------------------------------------
// Problems
// ---------------------------------------------------------------------------

export async function getProblems(): Promise<Problem[]> {
  const { data } = await api.get<ApiResponse<Problem[]>>('/api/problems');
  return data.data;
}

export async function getProblem(id: string): Promise<Problem> {
  const { data } = await api.get<ApiResponse<Problem>>(`/api/problems/${id}`);
  return data.data;
}

// ---------------------------------------------------------------------------
// Attempts
// ---------------------------------------------------------------------------

export async function createAttempt(problemId: string, learnerId = 'demo-learner'): Promise<Attempt> {
  const { data } = await api.post<ApiResponse<Attempt>>('/api/attempts', {
    problem_id: problemId,
    learner_id: learnerId,
  });
  return data.data;
}

export async function getAttempt(attemptId: string): Promise<Attempt> {
  const { data } = await api.get<ApiResponse<Attempt>>(`/api/attempts/${attemptId}`);
  return data.data;
}

export async function getAttempts(learnerId = 'demo-learner'): Promise<Attempt[]> {
  const { data } = await api.get<ApiResponse<Attempt[]>>('/api/attempts', {
    params: { learner_id: learnerId },
  });
  return data.data;
}

export async function deleteAttempt(attemptId: string): Promise<void> {
  await api.delete(`/api/attempts/${attemptId}`);
}

// ---------------------------------------------------------------------------
// Submissions
// ---------------------------------------------------------------------------

export async function submitSolution(attemptId: string, submission: SubmissionRequest): Promise<Evaluation> {
  const { data } = await api.post<ApiResponse<Evaluation>>(
    `/api/attempts/${attemptId}/submissions`,
    submission
  );
  return data.data;
}

// ---------------------------------------------------------------------------
// Evaluation
// ---------------------------------------------------------------------------

export async function getEvaluation(attemptId: string): Promise<Evaluation> {
  const { data } = await api.get<ApiResponse<Evaluation>>(`/api/attempts/${attemptId}/evaluation`);
  return data.data;
}

export async function retryEvaluation(attemptId: string): Promise<Evaluation> {
  const { data } = await api.post<ApiResponse<Evaluation>>(
    `/api/attempts/${attemptId}/evaluation/retry`
  );
  return data.data;
}

export async function checkHealth(): Promise<boolean> {
  try {
    await api.get('/api/health');
    return true;
  } catch {
    return false;
  }
}

// ---------------------------------------------------------------------------
// Error extractor
// ---------------------------------------------------------------------------

export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const msg = error.response?.data?.message;
    if (msg) return msg;
    if (error.code === 'ECONNABORTED') return 'Request timed out. Please try again.';
    if (!error.response) return 'Cannot connect to server. Is the backend running?';
  }
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred.';
}
