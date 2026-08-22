import { apiClient } from './client';

export interface EvaluationScenario {
  id?: string;
  user_input: string;
  conversation_steps?: Record<string, unknown>[];
  expected_behavior?: Record<string, unknown>[];
  validation_rules?: Record<string, unknown>[];
  tags?: string[];
  grounding?: GroundingSpec;
}

export interface GroundingSpec {
  enabled: boolean;
  reference_context: string;
  required_facts?: string[];
  forbidden_claims?: string[];
  answerable?: boolean;
  require_abstention_when_unanswerable?: boolean;
  min_sentence_overlap?: number;
  max_unsupported_sentences?: number;
}

export interface EvaluationRequest {
  agent_id: string;
  agent_version_id?: string;
  endpoint_url: string;
  scenario: EvaluationScenario;
  timeout_seconds?: number;
  headers?: Record<string, string>;
  input_field?: string;
  include_conversation?: boolean;
}

export interface EvaluationCheck {
  name: string;
  passed: boolean;
  message: string;
  evidence?: unknown;
  severity: string;
}

export interface EvaluationResponse {
  evaluation_id: string;
  execution_id: string;
  scenario_id: string;
  status: string;
  passed: boolean;
  score: number;
  checks: EvaluationCheck[];
  failure_type?: string | null;
  severity?: string | null;
  output_data?: Record<string, unknown> | null;
  error_message?: string | null;
  duration_seconds?: number | null;
  metadata: Record<string, unknown>;
}

export interface ReliabilitySummary {
  total: number;
  passed: number;
  failed: number;
  pass_rate: number;
  average_score: number;
  failure_types: Record<string, number>;
}

export interface EvaluationBatchResponse {
  evaluations: EvaluationResponse[];
  summary: ReliabilitySummary;
}

export interface GroundingRequest {
  answer: string;
  reference_context: string;
  required_facts?: string[];
  forbidden_claims?: string[];
  answerable?: boolean;
  require_abstention_when_unanswerable?: boolean;
  min_sentence_overlap?: number;
  max_unsupported_sentences?: number;
}

export interface GroundingEvidence {
  claim: string;
  evidence?: string | null;
  overlap: number;
  supported: boolean;
}

export interface GroundingResponse {
  grounded: boolean;
  score: number;
  evidence: GroundingEvidence[];
  unsupported_sentences: string[];
  missing_required_facts: string[];
  forbidden_claims_detected: string[];
  abstention_ok?: boolean | null;
  caveat: string;
}

export interface EvaluationHistoryItem {
  id: string;
  execution_id: string;
  evaluation_id: string;
  agent_id: string;
  agent_version_id?: string | null;
  scenario_id: string;
  status: string;
  passed: boolean;
  score: number;
  failure_type?: string | null;
  severity?: string | null;
  duration_seconds?: number | null;
  created_at: string;
}

export const evaluationsApi = {
  run: (request: EvaluationRequest) =>
    apiClient.post<EvaluationResponse>('/api/v1/evaluations/run', request),
  runBatch: (requests: EvaluationRequest[]) =>
    apiClient.post<EvaluationBatchResponse>('/api/v1/evaluations/batch', requests),
  grounding: (request: GroundingRequest) =>
    apiClient.post<GroundingResponse>('/api/v1/evaluations/grounding', request),
  history: (agentId: string, params?: { limit?: number; offset?: number }) =>
    apiClient.get<EvaluationHistoryItem[]>(`/api/v1/evaluations/agents/${agentId}/history`, params),
};
