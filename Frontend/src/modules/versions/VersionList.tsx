/**
 * Version List Component
 * Displays version history for an agent
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { versionsApi } from '../../api';
import type { PaginatedVersions } from '../../types';

interface VersionListProps {
  agentId: string;
}

export default function VersionList({ agentId }: VersionListProps) {
  const [versions, setVersions] = useState<PaginatedVersions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [expandedVersion, setExpandedVersion] = useState<string | null>(null);

  const loadVersions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await versionsApi.list(agentId, { page, page_size: 10 });
      setVersions(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load versions');
    } finally {
      setLoading(false);
    }
  }, [agentId, page]);

  useEffect(() => {
    void loadVersions();
  }, [loadVersions]);

  const handleCreateVersion = async () => {
    const notes = prompt('Enter version notes (optional):');
    if (notes === null) return; // User cancelled
    
    try {
      await versionsApi.create(agentId, { notes: notes || undefined });
      await loadVersions();
    } catch (err: any) {
      alert(err.message || 'Failed to create version');
    }
  };

  const toggleExpand = (versionId: string) => {
    setExpandedVersion(expandedVersion === versionId ? null : versionId);
  };

  if (loading && !versions) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-600">Loading versions...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
        <button
          onClick={loadVersions}
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
        <h3 className="text-xl font-semibold text-gray-900">Version History</h3>
        <button
          onClick={handleCreateVersion}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Create Snapshot
        </button>
      </div>

      {/* Version List */}
      {versions && versions.items.length === 0 ? (
        <div className="text-center py-8 text-gray-600">
          No versions yet. Create your first snapshot.
        </div>
      ) : (
        <div className="space-y-3">
          {versions?.items.map((version) => (
            <div
              key={version.id}
              className="bg-white border border-gray-200 rounded-lg overflow-hidden"
            >
              <div
                className="p-4 cursor-pointer hover:bg-gray-50"
                onClick={() => toggleExpand(version.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded font-mono text-sm">
                      v{version.version_number}
                    </span>
                    <div>
                      <p className="text-sm text-gray-600">
                        {new Date(version.created_at).toLocaleString()}
                      </p>
                      {version.notes && (
                        <p className="text-sm text-gray-700 mt-1">{version.notes}</p>
                      )}
                    </div>
                  </div>
                  <span className="text-gray-400">
                    {expandedVersion === version.id ? '▼' : '▶'}
                  </span>
                </div>
              </div>

              {/* Expanded Snapshot View */}
              {expandedVersion === version.id && (
                <div className="border-t border-gray-200 bg-gray-50 p-4">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">
                    Snapshot Details:
                  </h4>
                  <pre className="bg-white border border-gray-200 rounded p-3 text-xs overflow-x-auto">
                    {JSON.stringify(version.snapshot, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {versions && versions.total > 0 && (
        <div className="flex items-center justify-between pt-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={!versions.has_prev}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600">
            Page {versions.page} ({versions.total} total)
          </span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={!versions.has_next}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
