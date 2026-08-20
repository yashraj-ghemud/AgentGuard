/**
 * Tool List Component
 * Displays tools registered for an agent
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { toolsApi } from '../../api';
import type { PaginatedTools, RiskLevel } from '../../types';

interface ToolListProps {
  agentId: string;
}

const getRiskColor = (riskLevel: RiskLevel): string => {
  switch (riskLevel) {
    case 'low':
      return 'bg-green-100 text-green-800';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800';
    case 'high':
      return 'bg-orange-100 text-orange-800';
    case 'critical':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

export default function ToolList({ agentId }: ToolListProps) {
  const [tools, setTools] = useState<PaginatedTools | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [expandedTool, setExpandedTool] = useState<string | null>(null);
  const [filter, setFilter] = useState<{
    risk_level?: string;
    is_destructive?: boolean;
  }>({});

  const loadTools = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await toolsApi.listByAgent(agentId, { ...filter, page, page_size: 10 });
      setTools(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load tools');
    } finally {
      setLoading(false);
    }
  }, [agentId, page, filter]);

  useEffect(() => {
    void loadTools();
  }, [loadTools]);

  const handleDelete = async (toolId: string) => {
    if (!confirm('Are you sure you want to delete this tool?')) return;
    
    try {
      await toolsApi.delete(toolId);
      await loadTools();
    } catch (err: any) {
      alert(err.message || 'Failed to delete tool');
    }
  };

  const toggleExpand = (toolId: string) => {
    setExpandedTool(expandedTool === toolId ? null : toolId);
  };

  if (loading && !tools) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-600">Loading tools...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
        <button
          onClick={loadTools}
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
        <h3 className="text-xl font-semibold text-gray-900">Tools</h3>
        <div className="text-sm text-gray-600">
          Total: {tools?.total || 0}
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <select
          value={filter.risk_level || ''}
          onChange={(e) => setFilter({ ...filter, risk_level: e.target.value || undefined })}
          className="px-3 py-2 border border-gray-300 rounded-md text-sm"
        >
          <option value="">All Risk Levels</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={filter.is_destructive === true}
            onChange={(e) => setFilter({ 
              ...filter, 
              is_destructive: e.target.checked ? true : undefined 
            })}
            className="rounded"
          />
          Destructive Only
        </label>
      </div>

      {/* Tool List */}
      {tools && tools.items.length === 0 ? (
        <div className="text-center py-8 text-gray-600">
          No tools found. Register tools for this agent.
        </div>
      ) : (
        <div className="space-y-3">
          {tools?.items.map((tool) => (
            <div
              key={tool.id}
              className="bg-white border border-gray-200 rounded-lg overflow-hidden"
            >
              <div
                className="p-4 cursor-pointer hover:bg-gray-50"
                onClick={() => toggleExpand(tool.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h4 className="text-lg font-semibold text-gray-900">
                        {tool.name}
                      </h4>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(tool.risk_level)}`}>
                        {tool.risk_level.toUpperCase()}
                      </span>
                    </div>
                    <div className="flex gap-2 mt-2 text-xs">
                      {tool.is_destructive && (
                        <span className="px-2 py-1 bg-red-50 text-red-700 rounded">
                          Destructive
                        </span>
                      )}
                      {tool.is_reversible && (
                        <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded">
                          Reversible
                        </span>
                      )}
                      {tool.requires_confirmation && (
                        <span className="px-2 py-1 bg-yellow-50 text-yellow-700 rounded">
                          Requires Confirmation
                        </span>
                      )}
                      {tool.timeout_seconds && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded">
                          Timeout: {tool.timeout_seconds}s
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(tool.id);
                      }}
                      className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
                    >
                      Delete
                    </button>
                    <span className="text-gray-400">
                      {expandedTool === tool.id ? '▼' : '▶'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Expanded Schema View */}
              {expandedTool === tool.id && (
                <div className="border-t border-gray-200 bg-gray-50 p-4 space-y-3">
                  <div>
                    <h5 className="text-sm font-semibold text-gray-700 mb-1">
                      Input Schema:
                    </h5>
                    <pre className="bg-white border border-gray-200 rounded p-2 text-xs overflow-x-auto">
                      {JSON.stringify(tool.input_schema, null, 2)}
                    </pre>
                  </div>
                  <div>
                    <h5 className="text-sm font-semibold text-gray-700 mb-1">
                      Output Schema:
                    </h5>
                    <pre className="bg-white border border-gray-200 rounded p-2 text-xs overflow-x-auto">
                      {JSON.stringify(tool.output_schema, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {tools && tools.total > 0 && (
        <div className="flex items-center justify-between pt-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={!tools.has_prev}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600">
            Page {tools.page}
          </span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={!tools.has_next}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
