/**
 * Agent Registry API
 */

import { apiClient } from './client';
import type {
  Agent,
  CreateAgentRequest,
  UpdateAgentRequest,
  PaginatedAgents,
} from '../types';

const BASE_PATH = '/api/v1/agents';

export const agentsApi = {
  /**
   * List all agents with optional filtering and pagination
   */
  list: async (params?: {
    status?: string;
    execution_mode?: string;
    workspace_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedAgents> => {
    return apiClient.get<PaginatedAgents>(BASE_PATH, params);
  },

  /**
   * Get a single agent by ID
   */
  get: async (agentId: string): Promise<Agent> => {
    return apiClient.get<Agent>(`${BASE_PATH}/${agentId}`);
  },

  /**
   * Create a new agent
   */
  create: async (data: CreateAgentRequest): Promise<Agent> => {
    return apiClient.post<Agent>(BASE_PATH, data);
  },

  /**
   * Update an existing agent
   */
  update: async (agentId: string, data: UpdateAgentRequest): Promise<Agent> => {
    return apiClient.patch<Agent>(`${BASE_PATH}/${agentId}`, data);
  },

  /**
   * Delete an agent (soft delete)
   */
  delete: async (agentId: string): Promise<void> => {
    return apiClient.delete<void>(`${BASE_PATH}/${agentId}`);
  },
};
