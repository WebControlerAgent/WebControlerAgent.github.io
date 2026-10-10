# Captain and Small-Agent Task Division Plan — Two-Agent Minimum

## Non-negotiable rule
**Every dispatched task must have at least two small agents: (1) a primary worker and (2) an independent checker.** Both work on the same task ID. The checker must independently inspect the requirements, output, or tests and submit its own evidence; merely copying the worker's report does not count. The Captain reviews both results. Complex tasks may receive more agents, but never fewer than two.

## Roster
- 9 Captains remain in place.
- Each Captain now has 10 child-agent roles: five execution/coordination roles plus five complementary checker roles.
- Planned roster: 90 child roles + 9 Captains = 99 registered roles.
- Registration does not mean the agents are live processes. Runtime adapters and dispatch enforcement still need implementation and test.

## Team role pairs

### Manager / Operations Captain
- planner + **plan-auditor**: decompose work; audit task graph and acceptance criteria.
- scheduler + **dependency-auditor**: order work; independently check dependency readiness.
- policy-checker + **authorization-auditor**: authorize scope; independently audit the decision.
- state-keeper + **state-auditor**: manage state; detect invalid transitions and conflicting claims.
- reporter + **evidence-auditor**: report progress; reconcile every claim with artifacts/logs.

### Researcher / Research Captain
- source-discovery + **source-cross-checker**: discover sources; independently verify relevance and authorization.
- fact-checker + **claim-verifier**: cross-check claims; independently validate key claims.
- analyst + **recommendation-reviewer**: prioritize findings; challenge whether recommendations follow from evidence.
- trend-researcher + **trend-verifier**: assess changes over time; verify dates and alternative explanations.
- research-reviewer + **citation-auditor**: review quality; audit source traceability and unsupported claims.

### Image Agent / Media Captain
- source-validator + **provenance-auditor**: validate origins and permitted usage.
- asset-preparer + **asset-quality-checker**: prepare assets; independently inspect format, dimensions, and quality.
- metadata-writer + **metadata-auditor**: create metadata/alt text; check accuracy against the actual asset.
- rights-checker + **license-verifier**: verify documented license and usage constraints.
- media-reviewer + **accessibility-reviewer**: review quality; independently check legibility and accessibility.

### Publisher / Publishing Captain
- content-builder + **content-reviewer**: prepare content; independently check brief and accuracy.
- frontend-worker + **frontend-reviewer**: implement UI; review the diff, responsiveness, and scope.
- release-worker + **release-auditor**: assemble release; audit release manifest and gates.
- deployment-checker + **deployment-smoke-tester**: check deployment; test published routes and core behavior.
- rollback-worker + **recovery-verifier**: prepare recovery; verify the recovery point and instructions.

### SEO Agent / SEO Captain
- keyword-researcher + **intent-validator**: group keywords; independently validate search intent.
- metadata-worker + **metadata-auditor**: inspect metadata; independently recheck URLs.
- internal-link-worker + **link-verifier**: find link issues; independently verify proposed fixes.
- sitemap-worker + **sitemap-cross-checker**: inspect sitemap; reconcile sitemap, canonical, and route inventory.
- indexing-diagnostics + **crawl-evidence-reviewer**: diagnose indexing signals; independently review evidence and uncertainty.

### QA Agent / Quality Captain
- functional-tester + **journey-reviewer**: test flows; independently check coverage and results.
- ui-tester + **visual-regression-checker**: test UI; compare agreed viewports and baseline evidence.
- seo-tester + **seo-independent-checker**: run technical SEO checks; independently repeat on changed URLs.
- performance-tester + **benchmark-reviewer**: measure performance; audit conditions and metric validity.
- release-gatekeeper + **release-evidence-auditor**: decide release gate; audit every required evidence item.

### Bug Hunter / Diagnostics Captain
- log-analyzer + **log-cross-checker**: inspect logs; independently correlate timestamps and runs.
- reproduction-agent + **reproduction-reviewer**: reproduce defect; independently repeat steps where possible.
- root-cause-analyst + **hypothesis-challenger**: rank causes; challenge with alternative explanations.
- regression-planner + **regression-reviewer**: propose regression checks; audit coverage.
- diagnostic-reviewer + **diagnosis-auditor**: review incident; audit confidence and missing evidence.

### Bug Solver / Repair Captain
- patch-agent + **patch-reviewer**: propose bounded fix; independently inspect the diff.
- test-agent + **test-independence-checker**: run tests; check they truly exercise the defect/fix.
- security-reviewer + **threat-model-reviewer**: inspect risks; independently check permissions and secrets boundaries.
- rollback-planner + **rollback-verifier**: plan recovery; verify recovery reference and steps.
- repair-reviewer + **acceptance-auditor**: review repair; map results to acceptance criteria.

### Idea Builder / Innovation Captain
- idea-researcher + **idea-fact-checker**: gather evidence; independently verify assumptions.
- opportunity-analyst + **scoring-reviewer**: score opportunity; challenge weights and assumptions.
- prototype-planner + **scope-reviewer**: define prototype; audit feasibility and acceptance criteria.
- experiment-agent + **measurement-auditor**: track experiment; audit baseline, metrics, and calculations.
- idea-reviewer + **experiment-reviewer**: recommend continue/pivot/stop; independently assess evidence.

## Dispatch procedure
1. Manager records the goal, authorized repository/site, constraints, and acceptance criteria.
2. Planner creates atomic tasks and dependencies.
3. Scheduler waits until dependencies are complete and resources/file locks are available.
4. Captain assigns a primary worker and an independent checker to the same task ID before dispatch. The dispatcher must reject a task with fewer than two assigned small agents.
5. Worker and checker return separate summaries, evidence, artifacts, and next actions. The checker must independently evaluate the result rather than copy the worker.
6. Captain reviews both. If they disagree or evidence is missing, task becomes VERIFYING/BLOCKED and is not marked complete.
7. QA performs additional independent release/regression checks where applicable; Publisher deploys only after required gates pass.
8. Manager coordinates cross-team handoffs and reports verified outcomes only.

## Task record requirements
Every task includes: task ID, site/repository, Captain, primary agent ID, checker agent ID, objective, allowed paths, constraints, success criteria, dependencies, status, and attempt count.
Each agent result includes: same task ID, agent ID, role (worker/checker), state, summary, independent evidence, artifact references, changed files, and next action.

## Concurrency, security, and failure rules
- No overlapping simultaneous writes to the same file; serialize writes or use disjoint scopes.
- One active site/release at a time until runtime proves safe scaling.
- External/browser work is read-only by default; agents only access authorized paths/tools.
- Secrets stay in GitHub Actions Secrets, never prompts, logs, artifacts, frontend bundles, JSON, or commits.
- Deploy, delete, rollback, credential changes, and external writes require authorization.
- Default retries: 3. Missing evidence or a missing partner blocks completion.
- WAITING = not eligible; CLAIMED = assigned; WORKING = executing; VERIFYING = review pending; COMPLETED = both results plus Captain approval; FAILED = attempted and failed; BLOCKED = cannot proceed; SKIPPED = explicitly unnecessary.

## Implementation phases
A. Update canonical contracts and pair routing (configuration work).
B. Update roster generator and runtime validator to enforce 90 child roles and 99 total roles.
C. Implement deterministic dispatcher that refuses tasks with fewer than two assigned agents.
D. Add first real checker-backed worker (Playwright QA) with retained artifacts.
E. Trial sandboxed code repair with independent patch review and test evidence.
F. Connect AI-backed Captain delegation only after provider secrets, budgets, and schema validation are configured.
G. Prove one full two-agent task from dispatch through independent review and Captain approval.

The role definitions are not proof of live execution. Do not claim the pair rule is operational until the dispatcher rejects a one-agent task and a two-agent test passes.
