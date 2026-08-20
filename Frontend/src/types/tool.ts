/**
 * Tool Registry Types
 */

export enum RiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export interface Tool {
  id: string;
  agent_id: string;
  name: string;
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
  risk_level: RiskLevel;
  is_destructive: boolean;
  is_reversible: boolean;
  requires_confirmation: boolean;
  timeout_seconds?: number;
  created_at: string;
  updated_at: string;
}

export interface RegisterToolRequest {
  name: string;
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
  risk_level: RiskLevel;
  is_destructive?: boolean;
  is_reversible?: boolean;
  requires_confirmation?: boolean;
  timeout_seconds?: number;
}

export interface UpdateToolRequest {
  input_schema?: Record<string, any>;
  output_schema?: Record<string, any>;
  risk_level?: RiskLevel;
  is_destructive?: boolean;
  is_reversible?: boolean;
  requires_confirmation?: boolean;
  timeout_seconds?: number;
}

export interface PaginatedTools {
  items: Tool[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}
