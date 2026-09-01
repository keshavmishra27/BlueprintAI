import type { IdeaRefinerResult } from "./types";

const API_BASE_URL = "http://127.0.0.1:8000/api/v1";
export async function getAnalyses(): Promise<any[]> {
  const response = await fetch(`${API_BASE_URL}/decisions`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return await response.json();
}

export async function getAnalysis(id: string): Promise<IdeaRefinerResult> {
  const response = await fetch(`${API_BASE_URL}/decisions/${id}`);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Decision not found");
    }
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();

  if (!data || typeof data !== "object") {
    throw new Error("Malformed Response: Data is not an object");
  }
  if (!data.id || !data.decision_fingerprint) {
    throw new Error("Malformed Response: Missing decision ID or fingerprint");
  }
  if (!data.architecture || !data.architecture.components) {
    throw new Error("Malformed Response: Missing architecture payload");
  }

  return data as IdeaRefinerResult;
}
