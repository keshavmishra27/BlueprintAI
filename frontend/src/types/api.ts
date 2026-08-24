export interface Governance {
  action: string;
  severity: string;
  scores: Record<string, number>;
}

export interface Component {
  name: string;
  type: string;
  description?: string;
}

export interface ArchitectureDecision {
  component: string;
  choice: string;
  rationale: string;
}

export interface Architecture {
  components: Component[];
  decisions: ArchitectureDecision[];
}

export interface Alternative {
  description: string;
  architecture: Architecture;
}

export interface Decision {
  id: string;
  version: number;
  architecture: Architecture;
  governance: Governance;
  alternatives: Alternative[];
  alignment: number | null;
  decision_fingerprint: string;
  graph_fingerprint: string;
  context_fingerprint: string;
  created_at: string;
}

export interface GapFinding {
  category: "MATCH" | "MISSING" | "MISMATCH" | "EXTRA" | "UNKNOWN" | "CONFLICT";
  expected: string;
  observed: string;
}

export interface Evidence {
  file: string;
  line?: number;
  content: string;
}

export interface GapReport {
  id: string;
  decision_id: string;
  repository_fingerprint: string;
  expected_architecture: Architecture;
  actual_architecture: {
    components: string[];
  };
  findings: GapFinding[];
  evidence: Evidence[];
  alignment_score: number;
  created_at: string;
}

export interface RefinementOption {
  problem_detected: string;
  preserved: string[];
  exploration: string;
}

export interface RefinementCreateResponse {
  options: RefinementOption[];
}
