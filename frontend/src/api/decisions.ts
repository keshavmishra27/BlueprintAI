import type { Decision } from '../types/api';
import { fetchJson } from './client';

export const analyzeIdea = async (idea: string): Promise<Decision> => {
  return fetchJson<Decision>('/api/v1/ideas/analyze', {
    method: 'POST',
    body: JSON.stringify({ idea, context: {} }),
  });
};

export const getDecision = async (id: string): Promise<Decision> => {
  return fetchJson<Decision>(`/api/v1/decisions/${id}`);
};

export const getDecisionHistory = async (id: string): Promise<Decision[]> => {
  return fetchJson<Decision[]>(`/api/v1/decisions/${id}/history`);
};
