# AIWCU — AI Agent Workspace / Web Controller Agent

> **Handoff document:** this README is the project memory for future ChatGPT sessions, contributors, and maintainers. Update the **Current Status**, **Latest Runs**, and **Next Steps** sections whenever work changes so the project can resume without relying on chat history.

Repository: `WebControlerAgent/WebControlerAgent.github.io`  
Product: GitHub Pages dashboard + GitHub Actions agent controller + optional secure Manager Chat bridge.  
Primary authorized test site: `kingdom-raw` → `kindgommangaraw/kindgommangaraw.github.io` → `https://jpmangaatlis.online/`.

## 1. Project goal

Build a practical AI Agent Workspace where the user can issue plain-language instructions in the website's Manager Chat and have a Manager plan and dispatch work to specialized agents. Agents should work on one authorized site at a time, produce evidence, and be checked by a separate independent checker before a Captain reviews the result.

The longer-term plan is to reuse and adapt suitable open-source agents rather than write every agent from scratch. The system should remain free-tier-friendly where practical, but model/runtime limits and provider terms still apply.

### Intended organization

The routing registry in `agents/task_routing.json` defines **9 Captain roles and 90 child-agent role definitions** (10 children per Captain). Role definitions and routing policy are not proof that every role is already an independently running AI process.

Captain teams:
- Manager / operations
- Research
- Image / media
- Publisher / frontend / release
- SEO
- QA / testing
- Bug hunter / diagnosis
- Bug solver / repair
- Idea builder / innovation

The intended task policy is at least two roles per task: a primary worker and a separate checker. Both must refer to the same task ID, provide independent evidence, and pass the contract gate. The Captain must review both. More agents may be added for complex tasks.

## 2. Safety and execution boundaries

These are deliberate project rules, not missing features to bypass:
- Only repositories/sites explicitly marked `enabled: true` and `authorized: true` in `controller/sites.json` may be processed.
- `one_active_site: true`: process one site at a time; do not overlap writes across sites.
- Do not put GitHub tokens, Gemini keys, or other secrets in browser code, public files, `VITE_*` variables, or committed configuration.
- The frontend may submit requests, display status, and poll results; privileged operations belong in GitHub Actions or a protected backend.
- The bounded coding worker creates a **patch proposal only**. It uses a disposable workspace/container and read-only target checkout. It must not push, merge, deploy, or modify the original target checkout.
- Patch path/risk checks are deterministic guardrails, not a complete security audit or replacement for human/Captain review.
- No automatic merge/deploy from the bounded proposal worker. Captain approval is required.
- A successful build/deployment means the dashboard build shipped; it does not prove Google indexing, live chat E2E, or successful autonomous work on a target website.
- Never claim indexing, traffic, browser testing, task completion, or successful agent execution without direct evidence.

## 3. Current status (last reviewed: 2026-10-17)

### Verified completed
- GitHub Pages build and deployment pipeline is operational.
- Agent role preparation and deterministic task/queue/contract foundations are present.
- Manager AI workflow calls Gemini from GitHub Actions using the `GEMINI_API_KEY` Actions secret; the secret is not intended for frontend use.
- Manager plans are persisted to `controller/manager_plan.json`.
- Manager workflow can dispatch `agent-command.yml`; issue-triggered Manager requests can receive a pending marker and later runtime completion/failure comment.
- A read-only QA worker exists at `controller/health_worker.py`; it checks the authorized live site and SEO endpoints twice (primary + independent checker). Failed or inconsistent evidence blocks approval.
- A read-only SEO worker exists at `controller/seo_worker.py`; it checks homepage metadata/canonical/robots and sitemap-related endpoints through deterministic checks, with an independent repeat pass.
- The SEO audit workflow produced a successful audit for `kingdom-raw`: homepage HTTP 200, title/meta description/canonical/robots metadata present, `/robots.txt` and `/sitemap.xml` returned HTTP 200, sitemap directive present, and five absolute sitemap `loc` entries. The primary and checker evidence matched and reported no findings in that run. This is only a technical endpoint audit, **not** a Google indexing guarantee.
- A bounded open-source coding adapter uses mini-SWE-agent with a local Ollama/Qwen3 model inside a Docker sandbox. It is configured for a patch artifact only; the model/API runtime is not granted target-repository write credentials.
- The bounded worker validates task schema, authorized site/repository match, allowed paths, and output location before execution.
- `controller/patch_review.py` performs a separate deterministic review for patch structure, changed paths, high-risk patterns, and diff-header/file-marker agreement.
- A regression test was added to block patches whose actual `---` / `+++` file markers disagree with their `diff --git` header.
- The secure chat bridge client is in `src/chat/secureBridge.ts`; the Cloudflare Worker implementation is in `worker/index.js`. The bridge design keeps GitHub token and chat key outside the public site.
- Runtime completion comments were corrected in commit `d11fdeeef4fdcd48330b52d0bcd9d2c0c294be85`: `assign` now reports “assignment recorded; execution not started”, and other non-claim actions report only a state transition instead of falsely claiming the autonomous pipeline completed.
- Existing browser QA workflow uses Playwright; its real end-to-end coverage still needs to be checked against the latest site behavior.

### Latest known successful runs
- **Deploy AIWCU Universe to GitHub Pages:** [run 39007689273](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39007689273) — SUCCESS, commit `65d9e8fa2f8645004e7813165ded7fb12af008c4`.
- **Bounded Code Worker Tests:** [run 39007689272](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39007689272) — SUCCESS, same commit.
- **Worker contract checks:** [run 39006275367](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39006275367) — SUCCESS.
- **Paired Read-only SEO Audit:** [run 39004193612](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39004193612) — SUCCESS; artifact had no SEO findings and was marked ready for Captain review.

### Still running / last observed
- **Bounded AI Worker (Patch Only), run 39007689304:** [SUCCESS](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39007689304). The worker executed, exported a patch, passed deterministic patch review, and uploaded an artifact.
- **Earlier Bounded AI Worker run 39007682449:** [SUCCESS](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39007682449) with an artifact as well.
- Latest artifact from run 39007689304: `worker-result.json` reports `READY_FOR_INDEPENDENT_CHECK`, changed file `index.html`, `repository_modified: false`, `write_access: false`, `automatic_merge: false`, and `automatic_deploy: false`. `patch-review.json` reports `READY_FOR_CAPTAIN_REVIEW`, but explicitly says human/AI code review is still required.
- The model attempted the edit twice: the first edit succeeded, the repeated command then failed its old-text assertion. The final patch still contains one scoped meta-description change and passed the deterministic path/risk review. The demo task has now been clarified to make the edit once and not change the canonical URL.
- Deployment success does not imply that the proposal was applied to the target website.

### Important known mismatch to resolve
The demo task `tasks/demo-bounded-code-proposal.json` targets the authorized Kingdom Raw repository, whose current homepage source includes MangaReader-style content and a canonical URL pointing at `https://kindgommangaraw.github.io/`, while the registry's live URL is `https://jpmangaatlis.online/`. This canonical/live-domain mismatch is a separate SEO issue and was deliberately kept outside the demo patch's allowed scope. The generated proposal changes only the meta description. **Do not apply that generated proposal until a Captain reviews the target content and decides whether the canonical/domain configuration is correct.** The task objective was clarified so the edit runs only once and the canonical URL is not touched. A proposal is not a deployed fix.

## 4. Important files and their roles

### Frontend / Manager chat
- `src/main.tsx` — main UI wiring and runtime/status connection.
- `src/chat/managerChat.ts` — local/fallback chat behavior.
- `src/chat/secureBridge.ts` — HTTPS client for `/command`, `/runtime`, and `/result`.
- `src/chat/README.md` — chat adapter notes.
- `public/status.json` — published dashboard/runtime status artifact.

### Controller and contracts
- `controller/manager_ai.py` — calls Gemini from the protected workflow; validates the returned action.
- `controller/manager_plan.json` — latest persisted Manager plan.
- `controller/dispatch.py`, `controller/engine.py`, `controller/agent_runtime.py`, `controller/agent_worker.py` — dispatch/runtime state and pipeline.
- `controller/prepare_agents.py` — prepares/registers role inventory.
- `controller/task_dispatcher.py`, `controller/worker_queue.py`, `controller/worker_contract.py` — assignment, queue, result-pair validation.
- `controller/health_worker.py` — deterministic read-only QA worker.
- `controller/seo_worker.py`, `controller/agent_checks.py` — deterministic SEO/health checks.
- `controller/open_source_worker_adapter.py` — bounded mini-SWE-agent adapter and sandbox controls.
- `controller/worker_execution_bridge.py` — validates routing then invokes the bounded coding adapter.
- `controller/patch_review.py` — independent deterministic patch scope/risk review.
- `controller/sites.json` — allowlisted site/repository registry.
- `agents/task_routing.json` — Captain/child roles, primary/checker pairs, routes, phase status and policy.
- `tasks/seo-audit.json`, `tasks/demo-bounded-code-proposal.json`, `tasks/demo-ui-review.json` — example task contracts.

### Secure bridge and workflows
- `worker/index.js` — Cloudflare Worker bridge source.
- `worker/README.md` — setup instructions for Cloudflare Worker and required secrets.
- `.github/workflows/manager-ai.yml` — protected Manager AI planning.
- `.github/workflows/agent-command.yml` — deterministic runtime dispatch and result reporting.
- `.github/workflows/bounded-worker.yml` — bounded coding proposal only.
- `.github/workflows/code-worker-tests.yml` — patch/worker tests.
- `.github/workflows/worker-contract-ci.yml` — worker contract checks.
- `.github/workflows/seo-audit-worker.yml` — read-only paired SEO audit.
- `.github/workflows/browser-use-readonly.yml` — read-only browser QA workflow.
- `.github/workflows/deploy.yml` — GitHub Pages build/deploy workflow.
- Other workflow files exist for dispatch, monitoring, proposal runtime, and site manager. Inspect their current YAML before changing trigger/permission behavior.

## 5. Manager Chat: intended flow and external setup

The intended real flow is:

1. User enters a plain-language instruction in the website's Manager Chat.
2. Frontend sends it over HTTPS to the separately deployed Cloudflare Worker bridge.
3. The bridge authenticates the private chat key and origin, then creates a GitHub issue/request.
4. `manager-ai.yml` calls the protected Manager AI workflow with `GEMINI_API_KEY`, creates a structured plan, and dispatches the runtime when action is not `none`.
5. `agent-command.yml` runs the deterministic pipeline and posts a result/failure comment to the originating issue.
6. Bridge polling returns issue comments to the chat UI.

### User-side setup still required for real browser chat E2E
GitHub Pages cannot host secrets. Deploy `worker/index.js` as a Cloudflare Worker and configure the exact values described in `worker/README.md`:
- secret `GITHUB_TOKEN`: fine-grained token limited to this controller repository and Issues read/write;
- secret `AIWCU_CHAT_KEY`: a long private random key;
- variable `ALLOWED_ORIGIN`: exact live website origin, no trailing slash.
Also ensure the GitHub Actions secret `GEMINI_API_KEY` is valid and available to this repository. Do not paste secrets into chat, commits, README, or frontend settings that get saved publicly.

Until the Worker is deployed/configured and a real browser command is verified end-to-end, describe Manager Chat runtime as **implemented but E2E unverified**, not complete. Longer runtime tasks can finish after the browser stops polling; check the linked GitHub issue/Actions run if needed.

## 6. Recent changes / implementation history

- `21a6711a241db060c26104a98a06445bdbadb501` — expanded paired SEO audit evidence checks.
- `1a28b39d5a1df97ccdc2e91cc1b28ff8a14fe5a2` — updated SEO fixtures for homepage and sitemap checks; worker contract tests and deployment passed.
- `13957f7ac6518af1d32a8afbf029cee9bbef6378` — hardened patch reviewer to compare diff headers with actual file markers.
- `65d9e8fa2f8645004e7813165ded7fb12af008c4` — added regression test proving mismatched file markers are blocked; code-worker tests and deployment passed.

Older secure-chat integration commits are documented in Git history; inspect `src/chat/secureBridge.ts`, `worker/index.js`, and the Manager/runtime workflows for the current source of truth rather than relying on commit summaries alone.

## 7. Next steps — do these in order

### Priority 1 — close the active bounded-worker run
1. Re-check runs [39007689304](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39007689304) and [39007682449](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39007682449).
2. Confirm whether the model/runtime step finishes, times out, or fails. If it fails, read the job logs and the redacted `*-agent-output.log` artifact before editing code.
3. Confirm the independent patch-review step and artifact upload actually ran.
4. Do not accept a patch solely because the workflow job is green; inspect `worker-result.json`, `patch-review.json`, changed paths, and the patch itself.

### Priority 2 — fix the demo task/source mismatch
1. Inspect the real homepage at `https://jpmangaatlis.online/` and the target repository's current `index.html`.
2. Rewrite `tasks/demo-bounded-code-proposal.json` so its objective refers only to evidence that really exists in that repository.
3. Keep the allowlist narrow, and preserve proposal-only behavior.
4. Run the worker and independent reviewer again; require Captain review. Do not merge/deploy the generated patch automatically.

### Priority 3 — verify and finish Manager Chat E2E
1. Verify Cloudflare bridge source and setup against `worker/README.md`.
2. Confirm the owner has deployed the Worker and configured secrets (we cannot configure their Cloudflare account from GitHub repository tools alone).
3. Verify `GEMINI_API_KEY` exists as a GitHub Actions secret; never request the key value.
4. Send one harmless test command from the live website; trace browser → Worker → Manager issue → Manager workflow → runtime workflow → result comment → chat polling.
5. Fix any failure at the exact step shown in logs; add/update tests and this README.

### Priority 4 — keep worker scope honest and expand carefully
- QA and SEO workers are currently deterministic, read-only checkers; they are not general LLM agents and do not edit target sites.
- Coding worker currently returns a patch proposal only.
- Next worker candidates: browser QA with Playwright, then repair proposal, SEO proposal, and release/deployment verification. Each must have a narrow contract, independent checker, evidence artifact, timeout, path allowlist, and explicit approval gate.
- Only after a worker is independently verified should it be connected to Manager dispatch. Avoid marking all 90 child roles as “running” just because role definitions exist.

### Priority 5 — tests and release discipline
1. Run the relevant Python tests and workflow contract tests.
2. Run the browser E2E suite where supported.
3. Deploy only after checks pass.
4. Verify the deployed URL and current workflow result.
5. Update the status below with the commit SHA, run links, test results, and unresolved blockers.

## 8. Quick resume checklist for a new ChatGPT session

Start here before asking the user to repeat context:
1. Read this README and `controller/README.md`, `worker/README.md`, and `src/chat/README.md`.
2. Check current GitHub Actions runs for this repository; queued/running states may have changed since this document was written.
3. Inspect the latest commit and relevant workflow logs/artifacts.
4. Continue from **Next steps** in priority order; do not redo completed tests unless a change requires them.
5. Make real repository changes when authorized and tools allow; report commit SHA and actual run results.
6. Never claim external Cloudflare setup or browser E2E was completed unless directly verified.
7. After each meaningful change, update this README in the same work session so progress survives context limits.

## 9. Latest status update template

Use this section after future work and keep it current:

- **Last updated:** 2026-10-17
- **README handoff commit:** `6429bcaa56dc61fd1e8aacf91efb2d726ca30005`; documentation deployment [39053447507 — SUCCESS](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39053447507).
- **Latest confirmed code-worker tests:** [39053495287 — SUCCESS](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39053495287), after the demo task was clarified.
- **Latest completed bounded worker:** [39007689304 — SUCCESS](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39007689304); artifact passed deterministic scope/risk review and still requires Captain review.
- **Fresh bounded worker run:** [39053495254](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39053495254) was still installing/preflighting Ollama + Qwen3 at last check; target checkout, task execution, patch review and artifact upload were pending.
- **Latest workflow accuracy fix:** `d11fdeeef4fdcd48330b52d0bcd9d2c0c294be85`; a new Pages workflow [39053543109](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39053543109) was pending at last check.
- **Manager chat E2E:** pending external Cloudflare Worker setup and a verified live command/result round trip.
- **Next immediate action:** close the fresh bounded-worker run; verify the workflow accuracy fix deploys; then validate the canonical/live-domain mismatch and test Manager chat E2E.
