export interface RepoJudgeMetadata {
  analysis_id: string;
  decision_id: string;
  decision_fingerprint: string;
  timestamp: string;
  schema_version: string;
  project_name: string;
  tech_stack: string[];
}

export interface Component {
  name: string;
  type: string;
  description?: string;
  unresolved?: boolean;
}

export interface Architecture {
  components: Component[];
  decisions: any[];
}

export interface RepoJudgeOverall {
  score: number;
  confidence: "High" | "Medium" | "Low";
  assessment: string;
}

export interface RepoJudgeCheck {
  name: string;
  status: "completed" | "failed" | "unavailable" | "skipped";
  summary: string;
  exit_code?: number;
}

export interface RepoJudgeLimitation {
  area: string;
  reason: string;
  impact: string;
  severity: "Critical" | "High" | "Medium" | "Low" | "Info";
}

export interface RepoJudgeEvidence {
  id: string;
  file_path?: string | null;
  line_start?: number | null;
  line_end?: number | null;
  symbol?: string | null;
  description: string;
  source_type: "workspace_inspection" | "search" | "git" | "terminal_tool" | "semantic_analysis";
}

export interface RepoJudgeFinding {
  id: string;
  title: string;
  severity: "Critical" | "High" | "Medium" | "Low" | "Info";
  classification: "Verified Finding" | "Probable Concern" | "Recommendation";
  category: string;
  explanation: string;
  impact: string;
  recommendation: string;
  evidence_ids: string[];
}

export interface GapReport {
  id: string;
  decision_id: string;
  decision_fingerprint: string;
  repository_fingerprint: string;
  expected_architecture: Architecture;
  actual_architecture: { components: Component[]; [key: string]: any };
  findings: RepoJudgeFinding[];
  evidence: RepoJudgeEvidence[];
  alignment_score: number;
  created_at: string;
}

export interface SemanticReport {
  metadata: RepoJudgeMetadata;
  overall: RepoJudgeOverall;
  checks: RepoJudgeCheck[];
  limitations: RepoJudgeLimitation[];
  evidence: RepoJudgeEvidence[];
  findings: RepoJudgeFinding[];
}

export type AssessmentStatus = "success" | "failure" | "unavailable";

export interface StructuralLayer {
  status: AssessmentStatus;
  report: GapReport | null;
}

export interface SemanticLayer {
  status: AssessmentStatus;
  report: SemanticReport | null;
}

export interface RepositoryAssessment {
  metadata: RepoJudgeMetadata;
  structural: StructuralLayer;
  semantic: SemanticLayer;
}

export interface RepoJudgeListItem {
  analysis_id: string;
  project_name: string;
  timestamp: string;
  overall_score: number;
  decision_id?: string;
}
