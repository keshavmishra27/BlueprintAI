import { RepositoryAssessment, RepoJudgeListItem } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8088";

export async function getAnalyses(): Promise<RepoJudgeListItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/analyses`);
  if (!response.ok) {
    throw new Error(`Failed to fetch analyses: ${response.statusText}`);
  }
  return response.json();
}

export async function getAnalysis(id: string): Promise<RepositoryAssessment> {
  const response = await fetch(`${API_BASE_URL}/api/analysis/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch analysis ${id}: ${response.statusText}`);
  }
  return response.json();
}
