'use client';

import { FormEvent, useState } from 'react';
import Link from 'next/link';
import { evaluationsApi, GroundingResponse } from '@/api/evaluations';

export default function GroundingPage() {
  const [answer, setAnswer] = useState('');
  const [referenceContext, setReferenceContext] = useState('');
  const [requiredFacts, setRequiredFacts] = useState('');
  const [forbiddenClaims, setForbiddenClaims] = useState('');
  const [answerable, setAnswerable] = useState(true);
  const [result, setResult] = useState<GroundingResponse | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setResult(null);

    if (!answer.trim() || !referenceContext.trim()) {
      setError('Provide both the model answer and the reference evidence.');
      return;
    }

    setLoading(true);
    try {
      const response = await evaluationsApi.grounding({
        answer: answer.trim(),
        reference_context: referenceContext.trim(),
        required_facts: requiredFacts.split('\n').map((value) => value.trim()).filter(Boolean),
        forbidden_claims: forbiddenClaims.split('\n').map((value) => value.trim()).filter(Boolean),
        answerable,
        require_abstention_when_unanswerable: true,
      });
      setResult(response);
    } catch (caught) {
      const message = caught && typeof caught === 'object' && 'message' in caught
        ? String((caught as { message: string }).message)
        : 'The grounding request failed.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <div className="mb-10 flex flex-wrap items-center justify-between gap-4">
          <div>
            <Link href="/" className="text-sm text-cyan-300 hover:text-cyan-200">← AgentGuard home</Link>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight">Grounding &amp; Hallucination Check</h1>
            <p className="mt-2 max-w-3xl text-slate-400">
              Compare a model answer with evidence you control. AgentGuard highlights unsupported claims, missing facts, forbidden claims, and missing abstention.
            </p>
          </div>
          <div className="rounded-2xl border border-cyan-400/20 bg-cyan-400/10 px-4 py-3 text-right">
            <p className="text-xs uppercase tracking-widest text-cyan-200">Method</p>
            <p className="mt-1 text-sm text-slate-200">Transparent · Explainable · Evidence-based</p>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <form onSubmit={submit} className="rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-2xl shadow-black/20">
            <h2 className="text-xl font-medium">Test input</h2>
            <p className="mt-1 text-sm text-slate-400">No example data is preloaded, so every result comes from your supplied evidence.</p>

            <label className="mt-6 block text-sm font-medium text-slate-300" htmlFor="answer">Model answer</label>
            <textarea id="answer" value={answer} onChange={(event) => setAnswer(event.target.value)} rows={8} placeholder="Paste the answer produced by your model…" className="mt-2 w-full resize-y rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-cyan-400 transition focus:ring-2" />

            <label className="mt-5 block text-sm font-medium text-slate-300" htmlFor="reference">Reference evidence</label>
            <textarea id="reference" value={referenceContext} onChange={(event) => setReferenceContext(event.target.value)} rows={8} placeholder="Paste trusted context, retrieved documents, database facts, or policy text…" className="mt-2 w-full resize-y rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-cyan-400 transition focus:ring-2" />

            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-slate-300" htmlFor="required">Required facts <span className="text-slate-500">(one per line)</span></label>
                <textarea id="required" value={requiredFacts} onChange={(event) => setRequiredFacts(event.target.value)} rows={5} placeholder="e.g. launched in 2025" className="mt-2 w-full resize-y rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-cyan-400 focus:ring-2" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300" htmlFor="forbidden">Forbidden claims <span className="text-slate-500">(one per line)</span></label>
                <textarea id="forbidden" value={forbiddenClaims} onChange={(event) => setForbiddenClaims(event.target.value)} rows={5} placeholder="e.g. HIPAA certified" className="mt-2 w-full resize-y rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm outline-none ring-cyan-400 focus:ring-2" />
              </div>
            </div>

            <label className="mt-5 flex items-center gap-3 text-sm text-slate-300">
              <input type="checkbox" checked={answerable} onChange={(event) => setAnswerable(event.target.checked)} className="h-4 w-4 rounded border-slate-700 bg-slate-950" />
              The supplied evidence should be enough to answer the question
            </label>

            {error && <div role="alert" className="mt-5 rounded-xl border border-rose-400/30 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">{error}</div>}
            <button disabled={loading} type="submit" className="mt-6 w-full rounded-xl bg-cyan-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-wait disabled:opacity-60">
              {loading ? 'Checking…' : 'Check grounding'}
            </button>
          </form>

          <section className="rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-2xl shadow-black/20" aria-live="polite">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-xl font-medium">Evidence report</h2>
                <p className="mt-1 text-sm text-slate-400">Each finding is tied to supplied text rather than a hidden “AI judge”.</p>
              </div>
              {result && <span className={`rounded-full px-3 py-1 text-xs font-semibold ${result.grounded ? 'bg-emerald-400/15 text-emerald-300' : 'bg-rose-400/15 text-rose-300'}`}>{result.grounded ? 'GROUNDED' : 'UNSUPPORTED'}</span>}
            </div>

            {!result ? (
              <div className="mt-10 rounded-2xl border border-dashed border-slate-700 px-5 py-12 text-center text-sm text-slate-500">Run a check to see claim-level evidence and failure reasons.</div>
            ) : (
              <>
                <div className="mt-8 flex items-end justify-between">
                  <div>
                    <p className="text-sm text-slate-400">Grounding score</p>
                    <p className="mt-1 text-5xl font-semibold tracking-tight">{Math.round(result.score * 100)}<span className="text-2xl text-slate-500">%</span></p>
                  </div>
                  <div className="text-right text-sm text-slate-400">
                    <p>Unsupported: <span className="text-slate-200">{result.unsupported_sentences.length}</span></p>
                    <p>Missing facts: <span className="text-slate-200">{result.missing_required_facts.length}</span></p>
                  </div>
                </div>

                {result.abstention_ok !== null && result.abstention_ok !== undefined && (
                  <div className="mt-5 rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm text-slate-300">Abstention: <strong>{result.abstention_ok ? 'appropriate' : 'missing'}</strong></div>
                )}

                <div className="mt-6 space-y-3">
                  {result.evidence.map((item) => (
                    <div key={item.claim} className="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
                      <div className="flex items-start justify-between gap-4"><p className="text-sm font-medium text-slate-200">{item.claim}</p><span className={item.supported ? 'text-emerald-300' : 'text-rose-300'}>{item.supported ? 'SUPPORTED' : 'UNSUPPORTED'}</span></div>
                      <p className="mt-2 text-xs text-slate-500">Overlap: {Math.round(item.overlap * 100)}%</p>
                      {item.evidence && <p className="mt-2 text-sm text-slate-400">Evidence: {item.evidence}</p>}
                    </div>
                  ))}
                </div>

                {result.forbidden_claims_detected.length > 0 && <div className="mt-5 rounded-xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">Forbidden claims: {result.forbidden_claims_detected.join(', ')}</div>}
                {result.missing_required_facts.length > 0 && <div className="mt-3 rounded-xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-200">Missing required facts: {result.missing_required_facts.join(', ')}</div>}

                <div className="mt-6 rounded-xl border border-cyan-400/15 bg-cyan-400/5 px-4 py-4 text-xs leading-5 text-slate-400">{result.caveat}</div>
              </>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
