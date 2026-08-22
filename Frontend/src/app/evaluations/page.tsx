'use client';

import { FormEvent, useState } from 'react';
import Link from 'next/link';
import { evaluationsApi, EvaluationResponse } from '@/api/evaluations';

const defaultEndpoint = process.env.NEXT_PUBLIC_AGENT_ENDPOINT || '';

export default function EvaluationsPage() {
  const [agentId, setAgentId] = useState('');
  const [agentVersionId, setAgentVersionId] = useState('');
  const [endpoint, setEndpoint] = useState(defaultEndpoint);
  const [userInput, setUserInput] = useState('');
  const [behaviorType, setBehaviorType] = useState('must_respond');
  const [description, setDescription] = useState('');
  const [forbiddenPhrase, setForbiddenPhrase] = useState('');
  const [result, setResult] = useState<EvaluationResponse | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setResult(null);
    if (!endpoint.trim()) {
      setError('Enter an HTTP agent endpoint before running the scenario.');
      return;
    }
    if (!agentId.trim()) {
      setError('Enter the UUID of the registered agent.');
      return;
    }
    if (!userInput.trim()) {
      setError('Enter a scenario input to evaluate.');
      return;
    }

    setLoading(true);
    try {
      const response = await evaluationsApi.run({
        agent_id: agentId.trim(),
        agent_version_id: agentVersionId.trim() || undefined,
        endpoint_url: endpoint.trim(),
        scenario: {
          user_input: userInput,
          expected_behavior: [
            {
              behavior_type: behaviorType,
              description: description || `Expected behavior: ${behaviorType}`,
              must_not_contain: forbiddenPhrase ? [forbiddenPhrase] : [],
            },
          ],
          validation_rules: [],
          tags: ['console-run'],
        },
        timeout_seconds: 60,
      });
      setResult(response);
    } catch (caught) {
      const message = caught && typeof caught === 'object' && 'message' in caught
        ? String((caught as { message: string }).message)
        : 'The evaluation request failed.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  const scorePercent = result ? Math.round(result.score * 100) : 0;

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-6xl px-6 py-10">
        <div className="mb-10 flex flex-wrap items-center justify-between gap-4">
          <div>
            <Link href="/" className="text-sm text-cyan-300 hover:text-cyan-200">← AgentGuard home</Link>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight">Evaluation console</h1>
            <p className="mt-2 max-w-2xl text-slate-400">
              Execute one red-team scenario against an HTTP agent and inspect deterministic, explainable checks.
            </p>
          </div>
          <Link href="/grounding" className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-right hover:bg-cyan-400/15">
            <p className="text-xs uppercase tracking-widest text-cyan-200">Need hallucination testing?</p>
            <p className="mt-1 text-sm text-slate-200">Open Grounding Console →</p>
          </Link>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.05fr_.95fr]">
          <form onSubmit={submit} className="rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-2xl shadow-black/20">
            <h2 className="text-xl font-medium">Scenario definition</h2>
            <p className="mt-1 text-sm text-slate-400">The endpoint is validated server-side with SSRF protection and timeout limits.</p>

            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-slate-300" htmlFor="agent-id">Agent ID</label>
                <input id="agent-id" value={agentId} onChange={(event) => setAgentId(event.target.value)} placeholder="UUID of the registered agent" required className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-cyan-400 transition focus:ring-2" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300" htmlFor="agent-version-id">Agent version ID <span className="text-slate-500">(optional)</span></label>
                <input id="agent-version-id" value={agentVersionId} onChange={(event) => setAgentVersionId(event.target.value)} placeholder="UUID of the version snapshot" className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-cyan-400 transition focus:ring-2" />
              </div>
            </div>

            <label className="mt-6 block text-sm font-medium text-slate-300" htmlFor="endpoint">Agent endpoint</label>
            <input id="endpoint" value={endpoint} onChange={(event) => setEndpoint(event.target.value)} placeholder="https://agent.example.com/run" required className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-cyan-400 transition focus:ring-2" />

            <label className="mt-5 block text-sm font-medium text-slate-300" htmlFor="input">Scenario input</label>
            <textarea id="input" value={userInput} onChange={(event) => setUserInput(event.target.value)} rows={5} placeholder="Enter the prompt or task you want to red-team…" required className="mt-2 w-full resize-y rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-cyan-400 transition focus:ring-2" />

            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-slate-300" htmlFor="behavior">Expected behavior</label>
                <select id="behavior" value={behaviorType} onChange={(event) => setBehaviorType(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-cyan-400 focus:ring-2">
                  <option value="must_respond">Must respond</option>
                  <option value="must_refuse">Must refuse</option>
                  <option value="must_clarify">Must clarify</option>
                  <option value="must_confirm">Must confirm</option>
                  <option value="must_not_use_tool">Must not use tool</option>
                  <option value="must_report_failure">Must report failure</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300" htmlFor="forbidden">Forbidden phrase <span className="text-slate-500">(optional)</span></label>
                <input id="forbidden" value={forbiddenPhrase} onChange={(event) => setForbiddenPhrase(event.target.value)} placeholder="Text the response must not contain" className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-cyan-400 focus:ring-2" />
              </div>
            </div>

            <label className="mt-5 block text-sm font-medium text-slate-300" htmlFor="description">Expectation description <span className="text-slate-500">(optional)</span></label>
            <input id="description" value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Describe what a good response looks like" className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-cyan-400 focus:ring-2" />

            {error && <div role="alert" className="mt-5 rounded-xl border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">{error}</div>}
            <button disabled={loading} type="submit" className="mt-6 w-full rounded-xl bg-cyan-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-wait disabled:opacity-60">
              {loading ? 'Running evaluation…' : 'Run evaluation'}
            </button>
          </form>

          <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-2xl shadow-black/20" aria-live="polite">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-xl font-medium">Evaluation result</h2>
                <p className="mt-1 text-sm text-slate-400">Every check includes evidence so failures can become actionable regressions.</p>
              </div>
              {result && <span className={`rounded-full px-3 py-1 text-xs font-semibold ${result.passed ? 'bg-emerald-400/15 text-emerald-300' : 'bg-rose-400/15 text-rose-300'}`}>{result.passed ? 'PASSED' : 'FAILED'}</span>}
            </div>

            {!result ? (
              <div className="mt-10 rounded-2xl border border-dashed border-slate-700 px-5 py-12 text-center text-sm text-slate-500">Run a scenario to see its score, failure classification, and evidence.</div>
            ) : (
              <>
                <div className="mt-8 flex items-end justify-between">
                  <div>
                    <p className="text-sm text-slate-400">Reliability score</p>
                    <p className="mt-1 text-5xl font-semibold tracking-tight">{scorePercent}<span className="text-2xl text-slate-500">%</span></p>
                  </div>
                  <div className="text-right text-sm text-slate-400"><p>Status: <span className="text-slate-200">{result.status}</span></p><p>Duration: <span className="text-slate-200">{result.duration_seconds?.toFixed(2) ?? '—'}s</span></p></div>
                </div>
                <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-800"><div className={`h-full rounded-full transition-all ${result.passed ? 'bg-emerald-400' : 'bg-rose-400'}`} style={{ width: `${scorePercent}%` }} /></div>
                {result.failure_type && <div className="mt-5 rounded-xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-200">Failure classification: <strong>{result.failure_type}</strong> · severity {result.severity}</div>}
                <div className="mt-6 space-y-3">
                  {result.checks.map((check) => (
                    <div key={check.name} className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                      <div className="flex items-start justify-between gap-4"><p className="text-sm font-medium text-slate-200">{check.name}</p><span className={check.passed ? 'text-emerald-300' : 'text-rose-300'}>{check.passed ? 'PASS' : 'FAIL'}</span></div>
                      <p className="mt-2 text-sm text-slate-400">{check.message}</p>
                    </div>
                  ))}
                </div>
              </>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
