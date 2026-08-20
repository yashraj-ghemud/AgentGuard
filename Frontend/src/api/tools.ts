/**
 * Tool Registry API
 */

import { apiClient } from './client';
import type {
  Tool,
  RegisterToolRequest,
  UpdateToolRequest,
  PaginatedTools,
} from '../types';

export const toolsApi = {
  /**
   * List all tools for an agent
   */
  listByAgent: async (
    agentId: string,
    params?: {
      risk_level?: string;
      is_destructive?: boolean;
      requires_confirmation?: boolean;
      page?: number;
      page_size?: number;
    }
  ): Promise<PaginatedTools> => {
    return apiClient.get<PaginatedTools>(
      `/api/v1/agents/${agentId}/tools`,
      params
    );
  },

  /**
   * Get a single tool by ID
   */
  get: async (toolId: string): Promise<Tool> => {
    return apiClient.get<Tool>(`/api/v1/tools/${toolId}`);
  },

  /**
   * Register a new tool for an agent
   */
  register: async (agentId: string, data: RegisterToolRequest): Promise<Tool> => {
    return apiClient.post<Tool>(`/api/v1/agents/${agentId}/tools`, data);
  },

  /**
   * Update an existing tool
   */
  update: async (toolId: string, data: UpdateToolRequest): Promise<Tool> => {
    return apiClient.patch<Tool>(`/api/v1/tools/${toolId}`, data);
  },

  /**
   * Delete a tool
   */
  delete: async (toolId: string): Promise<void> => {
    return apiClient.delete<void>(`/api/v1/tools/${toolId}`);
  },
};
