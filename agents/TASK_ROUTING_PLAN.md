# Captain and Small-Agent Task Division Plan

## Status
This defines task ownership and routing for the registered 9 Captains and 45 child roles. It is a plan, not proof that agents are already executing. A task is complete only after its worker runs and saves evidence.

## Dispatch chain
Manager -> Captain -> primary child agent -> Captain review -> Manager integration. Each task has one primary owner. Cross-team work needs Manager approval. Parallel tasks are allowed only when dependencies are met and file/resource scopes do not overlap.

## Captain teams and assignments

### Manager / Operations
- **planner:** split goals into atomic tasks, dependencies, and acceptance criteria.
- **scheduler:** order eligible work and enforce one active site/release at a time.
- **policy-checker:** verify authorization, allowed scope, and safety constraints.
- **state-keeper:** validate saved states and prevent conflicting claims.
- **reporter:** report only verified outcomes and link evidence.
Output: approved task graph, dispatch order, policy decision, final report.

### Researcher / Research
- **source-discovery:** find relevant authorized sources.
- **fact-checker:** verify claims and resolve conflicts.
- **analyst:** prioritize evidence-backed findings.
- **trend-researcher:** compare dated patterns.
- **research-reviewer:** check evidence quality and traceability.
Output: source-backed brief, confidence notes, open questions.

### Image Agent / Media
- **source-validator:** verify provenance and permitted usage.
- **asset-preparer:** process approved assets into required formats.
- **metadata-writer:** write filenames, descriptions, accurate alt text.
- **rights-checker:** confirm documented usage rights; block unclear assets.
- **media-reviewer:** check quality, consistency, accessibility, compliance.
Output: asset manifest, metadata, rights notes, review decision.

### Publisher / Publishing
- **content-builder:** prepare scoped content/data changes.
- **frontend-worker:** implement approved UI/CSS/JS changes.
- **release-worker:** prepare release candidate and record commit/rollback point.
- **deployment-checker:** verify Actions and published status.
- **rollback-worker:** prepare recovery; execute only when authorized.
Output: changed files, build evidence, release/deployment references, recovery plan.

### SEO Agent / SEO
- **keyword-researcher:** group search terms by intent from permitted evidence.
- **metadata-worker:** check titles, descriptions, canonicals, robots, headings.
- **internal-link-worker:** find broken links and suggest improvements.
- **sitemap-worker:** validate sitemap parsing, URL coverage, canonical consistency.
- **indexing-diagnostics:** diagnose crawl/indexing evidence without promising indexing.
Output: URL-level audit and prioritized fixes.

### QA Agent / Quality
- **functional-tester:** test user journeys against acceptance criteria.
- **ui-tester:** check responsive layout, interactions, visual regressions.
- **seo-tester:** verify technical SEO on changed pages.
- **performance-tester:** measure performance with recorded test conditions.
- **release-gatekeeper:** aggregate evidence and PASS/BLOCK the release.
Output: test matrix, defects, metrics, release decision.

### Bug Hunter / Diagnostics
- **log-analyzer:** identify relevant failure signals and timestamps.
- **reproduction-agent:** reproduce issue and record expected/actual behavior.
- **root-cause-analyst:** rank causes using supporting/contradicting evidence.
- **regression-planner:** define tests to catch recurrence.
- **diagnostic-reviewer:** review completeness and confidence.
Output: reproducible report, likely cause, confidence, regression plan.

### Bug Solver / Repair
- **patch-agent:** propose the smallest safe fix in approved files.
- **test-agent:** run targeted checks and report exact results.
- **security-reviewer:** inspect permissions, secrets handling, scope risks.
- **rollback-planner:** record known-good reference and recovery steps.
- **repair-reviewer:** review patch, tests, and regression evidence.
Output: bounded patch, test evidence, security decision, rollback plan.

### Idea Builder / Innovation
- **idea-researcher:** gather evidence for proposed feature/site.
- **opportunity-analyst:** score value, feasibility, cost, risk, uncertainty.
- **prototype-planner:** define a small experiment and acceptance criteria.
- **experiment-agent:** record approved baseline, measurements, observation window.
- **idea-reviewer:** recommend continue/pivot/stop based on evidence.
Output: ranked ideas and experiment proposal; no production edits without Manager approval.

## How work is divided
1. Manager records the goal, authorized repository/site, constraints, and success criteria.
2. Planner breaks it into small, independently reviewable tasks.
3. Policy Checker blocks unclear authorization/scope, secret exposure, or unapproved destructive actions.
4. Scheduler builds dependencies and orders ready tasks.
5. Manager chooses one Captain; that Captain assigns one primary child and may create separate review/test tasks.
6. Child returns a structured result with evidence and artifacts.
7. Captain verifies acceptance criteria and requests rework when needed.
8. Manager coordinates team handoffs; QA independently verifies changes; Publisher releases only after gates pass.
9. Reporter records completed, blocked, failed, skipped, and unverified work.

## Default task flows
- Feature/visual change: Manager -> Researcher if needed -> Image Agent if assets -> Publisher -> QA -> SEO if URLs/content changed -> Manager.
- Bug fix: user/QA report -> Bug Hunter -> Bug Solver -> independent QA -> Publisher after PASS -> Manager.
- SEO issue: SEO diagnosis -> Researcher if needed -> approved Publisher fix -> QA SEO test -> SEO re-check -> Manager.
- New idea: Idea Builder -> Manager approval -> prototype work only if approved.
- Release: Publisher candidate -> QA gate -> deployment verification -> Manager report.

## Task/result contract
Task fields: `task_id`, `parent_task_id`, `site`, `repository`, `parent_captain`, `agent_id`, `objective`, `allowed_paths`, `constraints`, `success_criteria`, `priority`, `depends_on`, `status`, `attempt`.
Result fields: `task_id`, `agent_id`, `state`, `summary`, `evidence[]`, `artifacts[]`, `changed_files[]`, `next_action`.

## Guardrails
- No overlapping simultaneous edits to the same file; serialize writes or separate scopes.
- External/browser research is read-only by default; workers access only approved paths/tools.
- Never put secret values in prompts, logs, artifacts, frontend bundles, JSON, or commits. Use Actions Secrets.
- Deploy, delete, rollback, credential changes, and external writes require an authorization gate.
- Default maximum retries: 3. Missing evidence means VERIFYING/BLOCKED, never COMPLETED.
- WAITING = not eligible; CLAIMED = assigned; WORKING = running; VERIFYING = checks pending; COMPLETED = acceptance criteria plus evidence passed; FAILED = attempted but failed; BLOCKED = cannot proceed; SKIPPED = explicitly unnecessary.

## Implementation phases
A. Contracts and routing map.
B. Deterministic Python dispatcher: validate task records, assign owners, enforce dependencies/states/file locks.
C. First real worker: Playwright smoke tests with retained artifacts.
D. Sandboxed repair worker with mandatory tests/review.
E. AI-backed Captain delegation after provider secrets/budgets and schema validation.
F. Prove one full Manager -> Captain -> child -> QA -> Publisher -> Manager run with logs and artifacts.

The 54 roles are registered definitions, not 54 active AI processes. Dispatcher and worker adapters still need to be implemented and run.
