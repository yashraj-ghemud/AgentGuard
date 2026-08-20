/**
 * Agent Versioning Types
 */

export interface AgentSnapshot {
  name: string;
  endpoint_url: string;
  execution_mode: string;
  risk_profile: Record<string, any>;
  metadata: Record<string, any>;
  [key: string]: any;
}

export interface AgentVersion {
  id: string;
  agent_id: string;
  version_number: number;
  snapshot: AgentSnapshot;
  notes?: string;
  created_at: string;
}

export interface CreateVersionRequest {
  notes?: string;
}

export interface PaginatedVersions {
  items: AgentVersion[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}
