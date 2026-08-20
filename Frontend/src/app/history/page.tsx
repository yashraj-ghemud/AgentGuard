'use client';

import Link from 'next/link';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { evaluationsApi, EvaluationHistoryItem } from '@/api/evaluations';

const defaultAgentId = '00000000-0000-0000-0000-000000000001';

export default function HistoryPage() {
  const [agentId, setAgentId] = useState(defaultAgentId);
  const [runs, setRuns] = useState<EvaluationHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadHistory = useCallback(async () => {
    if (!agentId.trim()) {
      setError('Enter an agent ID to load history.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      setRuns(await evaluationsApi.history(agentId.trim(), { limit: 100 }));
    } catch (caught) {
      const message = caught && typeof caught === 'object' && 'message' in caught
        ? String((caught as { message: string }).message)
        : 'Could not load evaluation history.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [agentId]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  const metrics = useMemo(() => {
    const passed = runs.filter((run) => run.passed).length;
    const score = runs.length ? runs.reduce((total, run) => total + run.score, 0) / runs.length : 0;
    const failures = runs.reduce<Record<string, number>>((result, run) => {
      if (run.failure_type) result[run.failure_type] = (result[run.failure_type] || 0) + 1;
      return result;
    }, {});
    return { passed, score, passRate: runs.length ? passed / runs.length : 0, failures };
  }, [runs]);

  const failureRows = Object.entries(metrics.failures).sort((a, b) => b[1] - a[1]);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <div className="flex flex-wrap items-end justify-between gap-5">
          <div>
            <Link href="/" className="text-sm text-cyan-300 hover:text-cyan-200">← AgentGuard home</Link>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight">Reliability history</h1>
            <p className="mt-2 max-w-2xl text-slate-400">Review durable evaluations, identify recurring failure types, and spot reliability drift before release.</p>
          </div>
          <Link href="/evaluations" className="rounded-xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 hover:bg-cyan-300">Run a new evaluation</Link>
        </div>

        <div className="mt-8 flex flex-col gap-3 rounded-2xl border border-slate-800 bg-slate-900 p-4 sm:flex-row sm:items-end">
          <div className="flex-1"><label htmlFor="history-agent-id" className="text-xs uppercase tracking-widest text-slate-500">Agent ID</label><input id="history-agent-id" value={agentId} onChange={(event) => setAgentId(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-cyan-400 focus:ring-2" /></div>
          <button onClick={() => void loadHistory()} disabled={loading} className="rounded-xl border border-slate-700 px-5 py-3 text-sm font-medium text-slate-200 hover:bg-slate-800 disabled:opacity-50">{loading ? 'Refreshing…' : 'Refresh history'}</button>
        </div>

        {error && <div role="alert" className="mt-5 rounded-xl border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">{error}</div>}

        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <Metric label="Runs" value={String(runs.length)} detail="Durable evaluation records" />
          <Metric label="Pass rate" value={`${Math.round(metrics.passRate * 100)}%`} detail={`${metrics.passed} passing runs`} />
          <Metric label="Average score" value={`${Math.round(metrics.score * 100)}%`} detail="Across loaded evaluations" />
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[.8fr_1.2fr]">
          <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
            <h2 className="text-lg font-medium">Failure clusters</h2>
            <p className="mt-1 text-sm text-slate-400">Prioritize the failure modes appearing most often.</p>
            <div className="mt-6 space-y-4">
              {failureRows.length === 0 ? <p className="rounded-xl border border-dashed border-slate-700 px-4 py-8 text-center text-sm text-slate-500">No failures recorded.</p> : failureRows.map(([name, count]) => <div key={name}><div className="flex justify-between text-sm"><span className="text-slate-300">{name}</span><span className="text-slate-500">{count}</span></div><div className="mt-2 h-2 rounded-full bg-slate-800"><div className="h-full rounded-full bg-rose-400" style={{ width: `${Math.min(100, count / runs.length * 100)}%` }} /></div></div>)}
            </div>
          </section>

          <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6">
            <h2 className="text-lg font-medium">Recent runs</h2>
            <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[650px] text-left text-sm"><thead className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-500"><tr><th className="px-3 py-3">Scenario</th><th className="px-3 py-3">Result</th><th className="px-3 py-3">Score</th><th className="px-3 py-3">Failure</th><th className="px-3 py-3">Created</th></tr></thead><tbody>{runs.map((run) => <tr key={run.id} className="border-b border-slate-800/70"><td className="px-3 py-4 font-mono text-xs text-slate-400">{run.scenario_id.slice(0, 12)}…</td><td className={run.passed ? 'px-3 py-4 text-emerald-300' : 'px-3 py-4 text-rose-300'}>{run.passed ? 'Passed' : 'Failed'}</td><td className="px-3 py-4">{Math.round(run.score * 100)}%</td><td className="px-3 py-4 text-slate-400">{run.failure_type || '—'}</td><td className="px-3 py-4 text-slate-500">{new Date(run.created_at).toLocaleString()}</td></tr>)}</tbody></table>{runs.length === 0 && <p className="py-10 text-center text-sm text-slate-500">No durable runs found for this agent.</p>}</div>
          </section>
        </div>
      </div>
    </main>
  );
}

function Metric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5"><p className="text-sm text-slate-400">{label}</p><p className="mt-2 text-3xl font-semibold">{value}</p><p className="mt-1 text-xs text-slate-500">{detail}</p></div>;
}
