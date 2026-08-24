import type { Decision, RefinementCreateResponse } from '../types/api';
import { fetchJson } from './client';

export const createRefinementOptions = async (
  decisionId: string, 
  gapReportId: string | null = null,
  newConstraint: string | null = null
): Promise<RefinementCreateResponse> => {
  return fetchJson<RefinementCreateResponse>('/api/v1/refinements/create', {
    method: 'POST',
    body: JSON.stringify({ decision_id: decisionId, gap_report_id: gapReportId, new_constraint: newConstraint }),
  });
};

export const applyRefinement = async (
  decisionId: string,
  gapReportId: string | null,
  appliedExploration: string,
  preserved: string[],
  problemDetected: string
): Promise<Decision> => {
  return fetchJson<Decision>('/api/v1/refinements/apply', {
    method: 'POST',
    body: JSON.stringify({
      decision_id: decisionId,
      gap_report_id: gapReportId,
      applied_exploration: appliedExploration,
      preserved: preserved,
      problem_detected: problemDetected
    }),
  });
};
