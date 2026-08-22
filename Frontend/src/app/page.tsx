'use client';

import Link from 'next/link';

const capabilities = [
  {
    title: 'Agent Registry',
    description: 'Register and version agents, then keep evaluation targets traceable.',
    href: '/agents',
  },
  {
    title: 'Scenario Evaluation',
    description: 'Run red-team scenarios against an HTTP agent and inspect explicit behavior checks.',
    href: '/evaluations',
  },
  {
    title: 'Grounding Check',
    description: 'Compare a model answer with trusted evidence and expose unsupported claims.',
    href: '/grounding',
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-6xl px-6 py-16">
        <section className="text-center">
          <p className="text-sm font-medium uppercase tracking-[0.25em] text-cyan-300">AI-agent reliability</p>
          <h1 className="mt-4 text-5xl font-bold tracking-tight sm:text-6xl">AgentGuard</h1>
          <p className="mx-auto mt-5 max-w-3xl text-lg leading-8 text-slate-400">
            Red-team AI agents, inspect behavior failures, and test whether generated answers are supported by evidence.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link href="/evaluations" className="rounded-xl bg-cyan-400 px-5 py-3 font-semibold text-slate-950 shadow-lg shadow-cyan-950/40 hover:bg-cyan-300">Run an evaluation</Link>
            <Link href="/grounding" className="rounded-xl border border-slate-700 bg-slate-900 px-5 py-3 font-semibold text-slate-100 hover:bg-slate-800">Check groundedness</Link>
          </div>
        </section>

        <section className="mt-16 grid gap-6 md:grid-cols-3" aria-label="Capabilities">
          {capabilities.map((capability) => (
            <Link key={capability.title} href={capability.href} className="rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-2xl shadow-black/10 transition hover:-translate-y-0.5 hover:border-cyan-400/30">
              <h2 className="text-xl font-semibold text-white">{capability.title}</h2>
              <p className="mt-3 text-sm leading-6 text-slate-400">{capability.description}</p>
              <p className="mt-5 text-sm font-medium text-cyan-300">Open →</p>
            </Link>
          ))}
        </section>

        <section className="mt-12 grid gap-6 lg:grid-cols-2">
          <div className="rounded-3xl border border-slate-800 bg-slate-900 p-7">
            <h2 className="text-xl font-semibold">How to use AgentGuard</h2>
            <div className="mt-5 space-y-4 text-sm leading-6 text-slate-400">
              <p><span className="text-slate-200">1.</span> Register the agent/version you want to test.</p>
              <p><span className="text-slate-200">2.</span> Run a red-team scenario against its HTTP endpoint.</p>
              <p><span className="text-slate-200">3.</span> For RAG or factual answers, open Grounding Check and supply trusted evidence.</p>
              <p><span className="text-slate-200">4.</span> Use required facts and forbidden claims to turn known failure modes into repeatable tests.</p>
            </div>
          </div>
          <div className="rounded-3xl border border-slate-800 bg-slate-900 p-7">
            <h2 className="text-xl font-semibold">What the grounding score means</h2>
            <p className="mt-5 text-sm leading-6 text-slate-400">
              The current checker is deliberately transparent: it compares answer text with the reference evidence you supply and reports unsupported sentences, missing facts, forbidden claims, and missing abstention. It is not a universal truth detector and should be combined with semantic evaluation or human review for high-stakes decisions.
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}
