import type { GapReport } from '../types/api';
import { fetchJson } from './client';

export const analyzeRepository = async (decisionId: string, repoPath: string): Promise<GapReport> => {
  return fetchJson<GapReport>('/api/v1/repositories/analyze', {
    method: 'POST',
    body: JSON.stringify({ decision_id: decisionId, repo_path: repoPath }),
  });
};
