# Small-Agent Task Division & Captain Dispatch Plan

## Purpose and honest status

This plan defines how the 9 Captains divide work across their 45 registered child-agent roles. It is a routing contract for the existing AIWCU repository, not proof that an LLM worker is already executing. Until a dispatch adapter runs and records evidence, tasks remain planned/queued.

## Core rule

**Manager -> Captain -> child agent(s) -> Captain review -> Manager integration.** A child agent never self-assigns across teams. Every task has one accountable owner, a bounded file/resource scope, acceptance criteria, dependencies, and evidence. Cross-team handoffs require Manager approval.

## Captain ownership and small-agent assignments

### 1. Manager — Operations Captain
- **planner:** convert the user goal into small tasks; define acceptance criteria and dependencies.
- **scheduler:** select eligible tasks, respect the active-site lock, and order work.
- **policy-checker:** confirm repository/site authorization, safety limits, and task scope before dispatch.
- **state-keeper:** validate persisted task/agent states and prevent conflicting claims.
- **reporter:** publish a progress summary based only on run logs, artifacts, and verified results.
- **Captain output:** approved task graph, dispatch order, policy decision, final status report.

### 2. Researcher — Research Captain
- **source-discovery:** find relevant authorized sources and repository evidence.
- **fact-checker:** verify claims and reconcile conflicting evidence.
- **analyst:** turn evidence into prioritized recommendations.
- **trend-researcher:** compare dated observations and changes over time.
- **research-reviewer:** check traceability, source quality, and completeness.
- **Captain output:** evidence-backed research brief with citations, confidence, and unresolved questions.

### 3. Image Agent — Media Captain
- **source-validator:** verify source provenance and permitted usage.
- **asset-preparer:** process approved assets into required formats/sizes.
- **metadata-writer:** write asset descriptions, filenames, and context-accurate alt text.
- **rights-checker:** confirm documented usage rights; block unclear assets.
- **media-reviewer:** inspect visual quality, consistency, accessibility, and compliance.
- **Captain output:** approved asset manifest, metadata, rights notes, and review result.

### 4. Publisher — Publishing Captain
- **content-builder:** prepare content/data updates within the approved task scope.
- **frontend-worker:** implement approved UI/CSS/JS changes.
- **release-worker:** assemble a release candidate and record its commit/rollback point.
- **deployment-checker:** verify GitHub Actions and published deployment status.
- **rollback-worker:** prepare recovery steps and execute rollback only when explicitly authorized.
- **Captain output:** changed-file list, build result, release reference, deployment evidence, recovery plan.

### 5. SEO Agent — SEO Captain
- **keyword-researcher:** group relevant terms by search intent using permitted evidence.
- **metadata-worker:** check titles, descriptions, canonical tags, robots directives, and headings.
- **internal-link-worker:** detect broken links and propose internal-link improvements.
- **sitemap-worker:** parse sitemap, check URL coverage and canonical consistency.
- **indexing-diagnostics:** diagnose crawl/indexing signals without promising indexing.
- **Captain output:** URL-level SEO audit, prioritized fixes, sitemap coverage and evidence.

### 6. QA Agent — Quality Captain
- **functional-tester:** test primary user journeys against acceptance criteria.
- **ui-tester:** check responsive layout, visual regressions, and interactions.
- **seo-tester:** verify technical SEO for changed pages.
- **performance-tester:** measure build/runtime performance using recorded conditions.
- **release-gatekeeper:** combine results and PASS/BLOCK the release based on explicit gates.
- **Captain output:** test matrix, defects, metrics, and release decision.

### 7. Bug Hunter — Diagnostics Captain
- **log-analyzer:** identify failure signals in available logs and timestamps.
- **reproduction-agent:** reproduce the reported issue and record expected vs actual behavior.
- **root-cause-analyst:** rank causes using supporting/contradicting evidence.
- **regression-planner:** define checks that would catch recurrence.
- **diagnostic-reviewer:** review the diagnosis and confidence before handing off.
- **Captain output:** reproducible incident report, likely root cause, confidence, and regression plan.

### 8. Bug Solver — Repair Captain
- **patch-agent:** propose the smallest safe fix in authorized files only.
- **test-agent:** run targeted tests and report exact commands/results.
- **security-reviewer:** inspect permissions, secret handling, injection risks, and scope.
- **rollback-planner:** identify a known-good commit and recovery steps before risky changes.
- **repair-reviewer:** review patch, tests, and regression evidence before QA.
- **Captain output:** bounded patch, test evidence, security decision, and rollback instructions.

### 9. Idea Builder — Innovation Captain
- **idea-researcher:** gather evidence for a proposed feature/site idea.
- **opportunity-analyst:** score user value, feasibility, costs, risk, and uncertainty.
- **prototype-planner:** define a small experiment with scope and acceptance criteria.
- **experiment-agent:** record approved baseline, measurements, and observation window.
- **idea-reviewer:** recommend continue/pivot/stop based on evidence.
- **Captain output:** ranked idea brief and an experiment proposal; no production changes without Manager approval.

## Task division algorithm

1. Manager records the request, authorized site/repository, goal, constraints, deadline/priority if supplied, and success criteria.
2. Planner decomposes the goal into atomic tasks. Each task should change or verify one outcome and be small enough to review independently.
3. Policy Checker blocks tasks with missing authorization, unclear scope, secrets exposure, destructive actions without approval, or prohibited source usage.
4. Scheduler creates a dependency graph. Tasks with no dependency may run in parallel only when their file/resource scopes do not overlap and the runtime has capacity.
5. Manager routes each task to exactly one Captain. That Captain selects one primary child owner and may assign independent review/testing subtasks to other children on its team.
6. Child agents return structured evidence, not just prose. Missing evidence means VERIFYING or BLOCKED, never COMPLETED.
7. Captain checks the child result against acceptance criteria, requests rework if needed, and submits a signed-off team result to Manager.
8. Manager coordinates cross-team handoffs. QA independently verifies changed behavior; Publisher releases only after required gates pass.
9. Reporter publishes a status summary with completed, blocked, failed, skipped, and unverified counts plus artifact/run links.

## Default handoff/dependency patterns

### New feature or visual update
Researcher (only if research is needed) -> Image Agent (if assets are involved) -> Publisher -> QA -> SEO Agent (if URLs/metadata/content discovery change) -> Manager final report.

### Bug fix
QA or user report -> Bug Hunter (logs + reproduction + root cause) -> Bug Solver (patch + tests + security review) -> QA (independent regression/release gate) -> Publisher (release only after PASS) -> Manager.

### SEO issue
SEO Agent (URL-level diagnosis) -> Researcher (if external facts/keyword evidence is needed) -> Publisher (approved implementation) -> QA SEO tester -> SEO Agent re-check -> Manager report. Google indexing is never guaranteed.

### New idea
Idea Builder -> Manager review -> approved prototype task -> Publisher/QA as needed. Ideation never gets to modify production by itself.

## Conflict prevention and execution limits

- One task = one primary owner. Reviewers are separate, named tasks.
- Do not let two workers edit the same file concurrently. Split by non-overlapping files or serialize edits.
- Start with a conservative limit: one active site/release at a time; bounded child-agent concurrency configurable in runtime.
- A child can only access approved paths and tools for its task. Read-only research is the default for external/browser workers.
- No secret values in prompts, artifacts, logs, frontend bundles, JSON, or commits. Use GitHub Actions Secrets.
- No deploy, delete, rollback, credential change, or external write action without the configured authorization gate.
- Retries are bounded (default 3), with a failure report after the final attempt.
- Every task/result must carry a unique task ID and link to commit, workflow run, test output, report, or other verifiable artifact.
- Status meanings: WAITING = not eligible yet; CLAIMED = assigned; WORKING = executing; VERIFYING = awaiting checks; COMPLETED = acceptance criteria and evidence pass; FAILED = attempted but failed; BLOCKED = cannot proceed; SKIPPED = explicitly not needed.

## Required task record

Each dispatched task should include:
- `task_id`, `parent_task_id` (if any), `site`, `repository`, `parent_captain`, `agent_id`
- `objective`, `allowed_paths`, `constraints`, `success_criteria`, `priority`
- `depends_on`, `status`, `attempt`, `created_at`
- result: `summary`, `evidence[]`, `artifacts[]`, `changed_files[]`, `next_action`

## Implementation phases

1. **Phase A — Contracts:** add and validate this division plan and machine-readable routing map.
2. **Phase B — Deterministic dispatcher:** Python validates task records, assigns Captain/child by route, enforces dependency/state/file-lock rules, and writes queue/state. No AI provider needed yet.
3. **Phase C — First real worker:** wire Playwright-based deterministic QA to a bounded task; store screenshots/reports as artifacts.
4. **Phase D — Repair worker:** only after isolated sandboxing and test gates, trial one coding agent on a small, reviewable patch.
5. **Phase E — AI-backed delegation:** configure provider secrets and budgets, then let Captains generate subtasks through a schema-validated adapter.
6. **Phase F — End-to-end acceptance:** prove one task flows Manager -> Captain -> child -> QA -> Publisher -> Manager with logs and artifacts before calling the system autonomous.

## Current implementation status

This plan and routing contract are design/configuration only until the dispatcher and worker adapters are implemented and run. The 54 role definitions do not mean 54 independent AI processes are already active.
