# Open-source agent copy and integration map

**Status: MAPPING_READY_NOT_INSTALLED.** This is the implementation plan only. The projects below have not been copied into this repository, installed, or run as AI workers.

## Recommended adoption order

1. **Playwright** — add deterministic browser tests first. It is a testing/automation framework, not an LLM agent; basic tests need no model key.
2. **mini-swe-agent** — trial one isolated bug-fix task in a disposable branch/worktree. Require patch + test evidence + independent review.
3. **browser-use** — use for bounded, read-only browser research and checks; store sources/screenshots/report as artifacts.
4. **dannwaneri/seo-agent** — optional read-only SEO audit after confirming its current requirements, data handling, and API budget. Some modules require paid provider/API access.
5. **LangGraph OR CrewAI** — defer until the task dispatcher has real worker adapters. Choose one orchestration framework only if the current Python task contract is no longer enough.

## Repository-to-Captain mapping

| Open-source project | AIWCU role mapping | Use in AIWCU | First implementation |
|---|---|---|---|
| [Playwright](https://github.com/microsoft/playwright) — Apache-2.0 | QA Captain: `functional-tester`, `ui-tester`, `visual-regression-checker`; Publisher: `deployment-smoke-tester`; Bug Hunter: `reproduction-agent` | Deterministic browser journeys, console/network checks, screenshots, smoke tests | Add a CI workflow/test folder; publish pass/fail + trace/screenshots as artifacts |
| [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) — MIT | Bug Solver: `patch-agent`; Bug Hunter: `root-cause-analyst`; Publisher: `frontend-worker` (only when task is code repair) | One bounded code task at a time; prepare patch and evidence | Run in isolated runner/worktree; no direct production deployment; open patch/PR for review |
| [browser-use](https://github.com/browser-use/browser-use) — MIT | Researcher: `source-discovery`, `fact-checker`; SEO: `indexing-diagnostics`; Image: `source-validator` | Browser-based research, visible-page checks, gathering evidence | Start read-only; restrict allowed domains and timeouts; return citations/URLs and artifact paths |
| [dannwaneri/seo-agent](https://github.com/dannwaneri/seo-agent) — MIT | SEO: `keyword-researcher`, `metadata-worker`, `internal-link-worker`; QA: `seo-tester` | Technical SEO audit and structured reports | Optional isolated audit job; use only required modules; never let it auto-publish fixes |
| [LangGraph](https://github.com/langchain-ai/langgraph) — MIT | Manager: `planner`, `scheduler`, `state-keeper`; cross-Captain task graph | Stateful branching, checkpoints, retries and human approval gates | Evaluate later as a possible orchestrator adapter; preserve AIWCU task/result JSON contract |
| [CrewAI](https://github.com/crewAIInc/crewAI) — MIT | Alternative for Manager + Captain delegation | Role-based collaboration and event-driven flows | Alternative to LangGraph, not an additional layer; do not install both in the first version |

## Two-agent rule

Every dispatched task keeps the existing minimum pair:
- **Worker:** performs the assigned bounded task.
- **Independent checker:** checks evidence, acceptance criteria, and regressions.
- **Captain:** accepts or rejects the result.
- **Manager:** coordinates dependencies and approves cross-team handoffs/releases.

Recommended pair examples:
- Code repair: mini-swe-agent patch worker + separate patch reviewer; Playwright/test evidence supports the review.
- UI/release: implementation worker + independent reviewer; Playwright smoke test provides deterministic evidence.
- SEO audit: SEO audit worker + SEO-independent-checker; fixes remain suggestions until separately approved.
- Browser research: browser-use researcher + source-cross-checker; sources must be recorded.

A tool is not automatically a second independent agent. Playwright supplies deterministic test evidence; it does not replace the human/AI checker role.

## How to bring code in safely

1. Review the source repository, its current LICENSE, dependencies, security notes, and data/privacy behavior.
2. Prefer installing a pinned package or running a pinned upstream checkout over copying the entire repository.
3. If code is copied, preserve its license/copyright/NOTICE files and identify the exact upstream commit in an attribution manifest.
4. Pin dependency versions; use a dedicated environment/container; apply timeouts and per-task allowed paths.
5. Keep model/API keys in GitHub Actions Secrets or the trusted runtime's secret store. Never put keys in browser JavaScript, public JSON, logs, or commits.
6. Default to read-only access. Code-writing workers work on a disposable branch/worktree and cannot deploy directly.
7. Return a standard result: `task_id`, `agent_id`, `state`, `summary`, `evidence`, `artifacts`, `changed_files`, `next_action`.
8. Run unit tests, dispatcher tests, and Playwright smoke tests before any release; require Captain/Manager approval.

## Hosting constraint

The website on GitHub Pages is static; it cannot host persistent background AI workers. Run worker jobs through GitHub Actions or a separate trusted runtime. Actions are event-driven/ephemeral, so they are suitable for task jobs but not always-on agents.

## Explicitly not done yet

- No third-party repository has been cloned or copied into AIWCU by this mapping.
- No LLM provider has been configured.
- No external worker adapter is active.
- The existing dispatcher prepares/validates assignments; it does not itself execute these third-party agents.
