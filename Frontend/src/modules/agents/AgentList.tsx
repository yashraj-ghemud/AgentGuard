/**
 * Agent List Component
 * Displays paginated list of agents with filtering
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { agentsApi } from '../../api';
import type { PaginatedAgents } from '../../types';

export default function AgentList() {
  const [agents, setAgents] = useState<PaginatedAgents | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState<{
    status?: string;
    execution_mode?: string;
  }>({});

  const loadAgents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await agentsApi.list({ ...filter, page, page_size: 10 });
      setAgents(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load agents');
    } finally {
      setLoading(false);
    }
  }, [page, filter]);

  useEffect(() => {
    void loadAgents();
  }, [loadAgents]);

  const handleDelete = async (agentId: string) => {
    if (!confirm('Are you sure you want to delete this agent?')) return;
    
    try {
      await agentsApi.delete(agentId);
      await loadAgents();
    } catch (err: any) {
      alert(err.message || 'Failed to delete agent');
    }
  };

  if (loading && !agents) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-600">Loading agents...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 m-4">
        <p className="text-red-800">Error: {error}</p>
        <button
          onClick={loadAgents}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Agents</h2>
        <div className="text-sm text-gray-600">
          Total: {agents?.total || 0}
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <select
          value={filter.status || ''}
          onChange={(e) => setFilter({ ...filter, status: e.target.value || undefined })}
          className="px-3 py-2 border border-gray-300 rounded-md"
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="archived">Archived</option>
        </select>

        <select
          value={filter.execution_mode || ''}
          onChange={(e) => setFilter({ ...filter, execution_mode: e.target.value || undefined })}
          className="px-3 py-2 border border-gray-300 rounded-md"
        >
          <option value="">All Modes</option>
          <option value="http">HTTP</option>
          <option value="sdk">SDK</option>
          <option value="browser">Browser</option>
          <option value="docker">Docker</option>
        </select>
      </div>

      {/* Agent List */}
      {agents && agents.items.length === 0 ? (
        <div className="text-center py-8 text-gray-600">
          No agents found. Create your first agent to get started.
        </div>
      ) : (
        <div className="grid gap-4">
          {agents?.items.map((agent) => (
            <div
              key={agent.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {agent.name}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {agent.metadata?.description || 'No description'}
                  </p>
                  <div className="flex gap-3 mt-2 text-xs text-gray-500">
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                      {agent.execution_mode}
                    </span>
                    <span className={`px-2 py-1 rounded ${
                      agent.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {agent.status}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDelete(agent.id)}
                    className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {agents && agents.total > 0 && (
        <div className="flex items-center justify-between pt-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={!agents.has_prev}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600">
            Page {agents.page}
          </span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={!agents.has_next}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
