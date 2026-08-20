# Adversarial Audit and Enhancement Backlog

## Cross-question review

| Question | Finding | Priority |
| --- | --- | --- |
| Can a hostname resolve to a private address after validation? | Yes. The previous validator checked literal IPs only, leaving DNS rebinding and private-hostname risks. | Critical |
| Can an attacker spoof execution identity? | The evaluation service hard-coded a zero UUID for `agent_id`, so execution records were not tied to a real registered agent. | High |
| Are evaluation results durable? | No. Results existed only in HTTP responses, preventing history, trend analysis, replay, and audit trails. | High |
| Can a large or abusive batch overwhelm the service? | Batch size was bounded, but execution was sequential without a server-wide concurrency or payload policy. | Medium |
| Does CI fail when checks fail? | Existing workflow used `|| echo` fallbacks for frontend checks, allowing broken builds to pass. | High |
| Is the seed script compatible with the ORM model? | The reserved `metadata` ORM fix left a stale `agent1.metadata` access in the seed script. | High |
| Does the frontend expose the new reliability workflow? | It had a single-run console but no history, baseline comparison, or CI artifact view. | Medium |
| Are authentication and authorization complete? | The repository has exception types but no end-to-end request authentication or workspace authorization middleware. | High |
| Can a fresh database resolve every migration dependency? | No. The Part 2 migration referenced a nonexistent revision identifier; it was corrected to the actual `001_initial` revision and the new evaluation-runs migration now resolves to head `20240820_2100`. | Critical |
| Are scenario generation APIs fully reliable? | The first audit found mismatched imports, async contracts, and enum assumptions; these were repaired, but generation still needs durable job execution. | High |
| Can release decisions be automated? | The deterministic evaluator and regression detector can now form the basis of a CI gate, but machine-readable artifacts and a CLI are still missing. | Medium |

## Suggested advanced features

The highest-value next iterations are DNS-aware SSRF resolution with connection pinning, durable evaluation and trace records, run history and trend APIs, JUnit/SARIF export, a CI command-line gate, signed webhook integration, workspace authentication, rate limiting, asynchronous job orchestration, richer JSONPath assertions, and dashboard views for regressions and failure clusters.

## Iteration plan

Iteration 1 hardened security, identity, seed compatibility, request limits, and CI behavior. Iteration 2 added durable execution records, trend history, and JUnit/SARIF-compatible exports. Iteration 3 improved the frontend around run history, regression comparison, and operational visibility. Iteration 4 validated configuration invariants, container readiness, migration resolution, frontend builds, and security boundaries with focused regression tests.
