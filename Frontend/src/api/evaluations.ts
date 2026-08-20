import { apiClient } from './client';

export interface EvaluationScenario {
  id?: string;
  user_input: string;
  conversation_steps?: Record<string, unknown>[];
  expected_behavior?: Record<string, unknown>[];
  validation_rules?: Record<string, unknown>[];
  tags?: string[];
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
  history: (agentId: string, params?: { limit?: number; offset?: number }) =>
    apiClient.get<EvaluationHistoryItem[]>(`/api/v1/evaluations/agents/${agentId}/history`, params),
};
