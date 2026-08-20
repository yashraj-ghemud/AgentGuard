/**
 * Home Page
 */

import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            AgentGuard
          </h1>
          <p className="text-xl text-gray-600 mb-2">
            Automated Red-Teaming & Reliability Engineering for AI Agents
          </p>
          <p className="text-sm text-gray-500">
            Part 1 - Foundation: Agent Registry, Versioning & Tool Management
          </p>
        </div>

        <div className="mb-6 flex justify-center gap-3">
          <Link href="/evaluations" className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow hover:bg-slate-800">Evaluation console</Link>
          <Link href="/history" className="rounded-xl bg-white px-4 py-2 text-sm font-medium text-slate-800 shadow hover:bg-slate-50">Reliability history</Link>
        </div>

        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {/* Agent Registry */}
          <Link
            href="/agents"
            className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow"
          >
            <div className="text-blue-600 mb-4">
              <svg
                className="w-12 h-12"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Agent Registry
            </h2>
            <p className="text-gray-600">
              Register and manage AI agents with configuration, execution modes, and risk profiles.
            </p>
          </Link>

          {/* Agent Versioning */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="text-purple-600 mb-4">
              <svg
                className="w-12 h-12"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Agent Versioning
            </h2>
            <p className="text-gray-600">
              Immutable snapshots of agent configurations for tracking changes over time.
            </p>
          </div>

          {/* Tool Registry */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="text-green-600 mb-4">
              <svg
                className="w-12 h-12"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Tool Registry
            </h2>
            <p className="text-gray-600">
              Risk-based tool management with JSON Schema validation and safety controls.
            </p>
          </div>
        </div>

        {/* Features */}
        <div className="mt-16 max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-8">
            Production-Ready Features
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                🔒 Comprehensive Security
              </h3>
              <p className="text-gray-600 text-sm">
                SSRF protection, size limits, timeout enforcement, and secure execution.
              </p>
            </div>
            <div className="bg-white rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                🏗️ Modular Architecture
              </h3>
              <p className="text-gray-600 text-sm">
                Clean module boundaries with event-driven communication patterns.
              </p>
            </div>
            <div className="bg-white rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                📊 Database Migrations
              </h3>
              <p className="text-gray-600 text-sm">
                Alembic-powered migrations with proper indexes and constraints.
              </p>
            </div>
            <div className="bg-white rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                🚀 CI/CD Pipeline
              </h3>
              <p className="text-gray-600 text-sm">
                Automated testing, linting, type checking, and security scanning.
              </p>
            </div>
          </div>
        </div>

        {/* API Documentation Link */}
        <div className="mt-12 text-center">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            View API Documentation
          </a>
        </div>
      </div>
    </div>
  );
}
