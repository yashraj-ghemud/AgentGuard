/**
 * Agent Registry Types
 */

export enum ExecutionMode {
  HTTP = 'http',
  SDK = 'sdk',
  BROWSER = 'browser',
  DOCKER = 'docker',
}

export enum EntityStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  ARCHIVED = 'archived',
}

export interface RiskProfile {
  max_tool_risk_level?: 'low' | 'medium' | 'high' | 'critical';
  allowed_tool_categories?: string[];
  blocked_domains?: string[];
  [key: string]: any;
}

export interface AgentMetadata {
  description?: string;
  tags?: string[];
  owner?: string;
  [key: string]: any;
}

export interface Agent {
  id: string;
  name: string;
  endpoint_url: string;
  execution_mode: ExecutionMode;
  status: EntityStatus;
  risk_profile: RiskProfile;
  metadata: AgentMetadata;
  workspace_id?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateAgentRequest {
  name: string;
  endpoint_url: string;
  execution_mode: ExecutionMode;
  risk_profile?: RiskProfile;
  metadata?: AgentMetadata;
  workspace_id?: string;
}

export interface UpdateAgentRequest {
  endpoint_url?: string;
  execution_mode?: ExecutionMode;
  status?: EntityStatus;
  risk_profile?: RiskProfile;
  metadata?: AgentMetadata;
}

export interface PaginatedAgents {
  items: Agent[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}
