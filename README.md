# AgentGuard

**AI-agent red-teaming, reliability testing, and groundedness checks**

AgentGuard is a modular platform for evaluating AI agents through adversarial scenarios, safe HTTP execution, deterministic behavior checks, regression comparison, and evidence-based groundedness analysis.

> **Important limitation:** AgentGuard's groundedness check is a transparent heuristic that compares model output with evidence supplied by the caller. It does not prove real-world truth and should not be treated as a universal hallucination detector.

## What You Can Test

- Register and version AI agents and their tools.
- Generate structured red-team scenarios from agent capabilities, risk profiles, and test strategy.
- Execute scenarios against HTTP agent endpoints with SSRF/private-network protections, request limits, and timeouts.
- Evaluate refusal, clarification, confirmation, tool-use, failure-reporting, text, regex, and JSON-field expectations.
- Run evidence-based groundedness checks for unsupported claims, missing required facts, forbidden claims, and missing abstention.
- Compare baseline and current reliability summaries for regression detection.
- Export evaluation batches as JUnit XML or SARIF for CI/security workflows.

## Architecture

AgentGuard uses a **modular monolith** with explicit boundaries between core services and feature modules.

```text
AgentGuard/
├── Backend/                  # FastAPI backend
│   ├── core/                # config, database, events, execution, LLM providers
│   ├── modules/             # agent, risk, scenario, evaluation modules
│   ├── shared/              # shared types and utilities
│   └── tests/               # backend tests
├── Frontend/                 # Next.js web console
├── docs/                     # architecture, security, evaluation documentation
├── docker-compose.yml
└── .github/workflows/        # CI
```

## Key API Endpoints

### Execute an evaluation

`POST /api/v1/evaluations/run`

Runs one scenario against an HTTP agent endpoint and returns an explainable set of checks.

### Check groundedness

`POST /api/v1/evaluations/grounding`

Example request:

```json
{
  "answer": "The system launched in 2025 and has 10 million users.",
  "reference_context": "The system launched in 2025 for public testing.",
  "required_facts": ["launched in 2025"],
  "forbidden_claims": ["10 million users"],
  "answerable": true
}
```

The response includes a score, unsupported sentences, missing facts, forbidden claims, and a limitation/caveat.

### Batch and regression APIs

- `POST /api/v1/evaluations/batch`
- `POST /api/v1/evaluations/compare`
- `POST /api/v1/evaluations/export/junit`
- `POST /api/v1/evaluations/export/sarif`
- `GET /api/v1/evaluations/agents/{agent_id}/history`

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker and Docker Compose

### Start the stack

```bash
git clone https://github.com/yashraj-ghemud/AgentGuard.git
cd AgentGuard
cp .env.example .env
make dev
```

The local API is available at `http://localhost:8000`; the FastAPI OpenAPI UI is at `http://localhost:8000/docs`.

### Test and quality checks

```bash
make test
make lint
make typecheck
```

For the frontend:

```bash
cd Frontend
npm ci
npm run type-check
npm run build
npm test
```

## Frontend Consoles

The web UI exposes:

- `/agents` for agent registration and management
- `/evaluations` for HTTP-agent scenario evaluation
- `/grounding` for standalone hallucination/groundedness checks
- `/history` for persisted evaluation history

The frontend reads its backend URL from `NEXT_PUBLIC_API_URL`.

## LLM Configuration

Scenario intelligence and generation use the configured LLM provider. The provider abstraction supports OpenAI and a mock provider for tests. Production/deployed environments must provide the required provider credentials; the mock provider is for development/testing and should not be presented as real model output.

## Security Controls

The execution path includes SSRF protection, private/metadata network blocking, request/response limits, timeout enforcement, input validation, and secret/header redaction.

See [docs/security.md](docs/security.md) and [docs/evaluation.md](docs/evaluation.md).

## Deployment

A Render deployment manifest is provided in [`render.yaml`](render.yaml). Deployed URLs are intentionally configured through deployment settings rather than documented as permanent public endpoints in this README.

## Project Status

This repository is prepared as a hackathon project. The supported functionality is the code and tests present in the current branch; future modules are tracked separately and are not described here as implemented.

## License

No license file is currently committed. Do not assume broad reuse rights unless a license is added.
