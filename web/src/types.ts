export type Node = {
  id: string;
  name: string;
  type: string;
  ticker?: string;
};

export type Edge = {
  source: string;
  target: string;
  criticality: number;
  substitutability: number;
  product: string;
};

export type Subgraph = { nodes: Node[]; edges: Edge[] };

export type ToolCall = {
  tool: string;
  input: Record<string, any>;
};

export type Spof = {
  id: string;
  name: string;
  type: string;
  min_hops: number;
  aggregated_impact: number;
  hidden_score: number;
  path_count: number;
  sample_paths: string[][];
};

export type CascadeHit = {
  company_id: string;
  company: string;
  ticker: string;
  impact: number;
  hops: number;
  chain: string[];
};

export type Entity = { id: string; name: string; type: string; score?: number };

export type AskResponse = {
  question: string;
  answer: string;
  trace: ToolCall[];
  turns: number;
  question_id: string;
  analysis_id: string;
  highlighted_ids: string[];
  paths: string[][];
  blindspot: Spof[] | null;
  cascade: CascadeHit[] | null;
  center_entity: Entity | null;
};

export type CritiqueResponse = {
  skeptic: string;
  skeptic_trace: ToolCall[];
};

export type PrecedentResponse = {
  historian: string;
  historian_trace: ToolCall[];
};

export type MemoryEntry = {
  id: string;
  role: string;
  ts: number;
  confidence: number;
  turns: number;
  question: string;
  entities: string[];
};
