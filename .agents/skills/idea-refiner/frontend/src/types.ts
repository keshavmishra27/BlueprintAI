export interface Governance {
  action: string;
  severity: string;
  scores: Record<string, number>;
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
  alignment?: number;
  decision_fingerprint: string;
  graph_fingerprint: string;
  context_fingerprint: string;
  created_at: string;
}

export interface IdeaRefinerResult extends Decision {}
