/**
 * Agent Versioning API
 */

import { apiClient } from './client';
import type {
  AgentVersion,
  CreateVersionRequest,
  PaginatedVersions,
} from '../types';

export const versionsApi = {
  /**
   * List all versions for an agent
   */
  list: async (
    agentId: string,
    params?: {
      page?: number;
      page_size?: number;
    }
  ): Promise<PaginatedVersions> => {
    return apiClient.get<PaginatedVersions>(
      `/api/v1/agents/${agentId}/versions`,
      params
    );
  },

  /**
   * Get a specific version by ID
   */
  get: async (agentId: string, versionId: string): Promise<AgentVersion> => {
    return apiClient.get<AgentVersion>(
      `/api/v1/agents/${agentId}/versions/${versionId}`
    );
  },

  /**
   * Get the latest version
   */
  getLatest: async (agentId: string): Promise<AgentVersion> => {
    return apiClient.get<AgentVersion>(
      `/api/v1/agents/${agentId}/versions/latest`
    );
  },

  /**
   * Get a version by its number
   */
  getByNumber: async (agentId: string, versionNumber: number): Promise<AgentVersion> => {
    return apiClient.get<AgentVersion>(
      `/api/v1/agents/${agentId}/versions/by-number/${versionNumber}`
    );
  },

  /**
   * Create a new version snapshot
   */
  create: async (
    agentId: string,
    data?: CreateVersionRequest
  ): Promise<AgentVersion> => {
    return apiClient.post<AgentVersion>(
      `/api/v1/agents/${agentId}/versions`,
      data
    );
  },
};
