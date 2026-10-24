# AIWCU — AI Agent Workspace / Web Controller Agent

> **Handoff document:** this README is the project memory for future ChatGPT sessions, contributors, and maintainers. Update the **Current Status**, **Latest Runs**, and **Next Steps** sections whenever work changes so the project can resume without relying on chat history.

Repository: `WebControlerAgent/WebControlerAgent.github.io`  
Product: GitHub Pages dashboard + GitHub Actions agent controller + GitHub-Issue-based Manager Chat handoff. GitHub-only: no Cloudflare, Supabase, or separate bridge required.  
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

## 3. Current status (last reviewed: 2026-10-24)

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
- Manager Chat uses a fine-grained personal access token to connect directly to GitHub Issues, verifies the account is `WebControlerAgent` and access to this repository, creates a `[Manager AI]` issue, and polls comments for the workflow response. The token exists only in React memory and clears on disconnect/reload; it is not stored in localStorage or committed. The token must be limited to this one repository with Issues read/write only. Because browser JavaScript can access it, this is less secure than a server-side token; never use a broad-scope token. Live deployment is verified. On 2026-10-18, the GitHub-only Manager Chat `hi` smoke test created issue #31, Manager AI run 39107674465 succeeded, and Agent Runtime run 39107686392 completed successfully. The issue thread currently contains the runtime pending marker plus the claim-pipeline success comment; confirm that the final runtime comment is rendered in the browser chat before treating full end-to-end chat display as verified.
- Runtime completion comments were corrected in commit `d11fdeeef4fdcd48330b52d0bcd9d2c0c294be85`: `assign` now reports “assignment recorded; execution not started”, and other non-claim actions report only a state transition instead of falsely claiming the autonomous pipeline completed.
- Existing browser QA workflow uses Playwright; its real end-to-end coverage still needs to be checked against the latest site behavior.

### Latest known successful runs
- **GitHub Pages deployment:** [run 40083596694](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/40083596694) — SUCCESS after the bounded worker trigger was changed.
- **Bounded code worker tests:** [run 40083596693](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/40083596693) — SUCCESS.
- **Paired read-only SEO audit:** [run 40083434908](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/40083434908) — SUCCESS.
- **SEO chat routing smoke test:** [run 40076686443](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/40076686443) — SUCCESS; this verified the issue-triggered workflow, not the complete website-browser chat round trip.

### Active / unverified
- **Bounded AI Worker (Patch Only), run 40083434881:** last checked IN PROGRESS in “Execute bounded worker and export proposal”; task authorization and target checkout passed, and Ollama/Qwen setup completed. The worker output, independent patch review, and artifact upload have not yet been confirmed. [Follow run 40083434881](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/40083434881).
- **Recent deployment and code tests:** latest deployment and test workflows are green, but this does not prove coding-worker success or full browser Manager Chat E2E.

### Important known mismatch to resolve
The demo task `tasks/demo-bounded-code-proposal.json` targets the authorized Kingdom Raw repository, whose current homepage source includes MangaReader-style content and a canonical URL pointing at `https://kindgommangaraw.github.io/`, while the registry's live URL is `https://jpmangaatlis.online/`. This canonical/live-domain mismatch is a separate SEO issue and was deliberately kept outside the demo patch's allowed scope. The generated proposal changes only the meta description. **Do not apply that generated proposal until a Captain reviews the target content and decides whether the canonical/domain configuration is correct.** The task objective was clarified so the edit runs only once and the canonical URL is not touched. A proposal is not a deployed fix.

## 4. Important files and their roles

### Frontend / Manager chat
- `src/main.tsx` — main UI wiring and runtime/status connection.
- `src/chat/managerChat.ts` — local/fallback chat behavior.
- `src/chat/githubDeviceFlow.ts` — scoped-token verification, account/repository verification, issue creation, and comment polling.
- `src/chat/secureBridge.ts` — legacy optional HTTPS bridge, unused by current chat.
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

## 5. Manager Chat: GitHub-only scoped-token connection

1. Create a **fine-grained personal access token** under the `WebControlerAgent` account.
2. Set **Resource owner** to `WebControlerAgent`; choose **Only select repositories** and select only `WebControlerAgent.github.io`.
3. Grant **Issues: Read and write** only. Do not grant Contents, Actions, Administration, or any other repository access.
4. In the deployed Manager Chat, paste the token into the password field and click **Connect GitHub**. The app verifies the account and target repository before enabling command submission.
5. The token stays in React component memory only; disconnecting or reloading clears it. It is not stored in localStorage, sessionStorage, or committed to source.
6. **Security limitation:** any token used by a public browser page is available to that page's JavaScript and may be exposed by malicious extensions or an XSS vulnerability. This is less secure than server-side token handling. Use only a repository-scoped token with the minimum permission, and revoke it in GitHub settings if you suspect exposure.

The issue-opened workflow uses the repository's Actions-side `GEMINI_API_KEY` and its own `GITHUB_TOKEN`; never paste either secret into the website.

## 6. Recent changes / implementation history

- `21a6711a241db060c26104a98a06445bdbadb501` — expanded paired SEO audit evidence checks.
- `1a28b39d5a1df97ccdc2e91cc1b28ff8a14fe5a2` — updated SEO fixtures for homepage and sitemap checks; worker contract tests and deployment passed.
- `13957f7ac6518af1d32a8afbf029cee9bbef6378` — hardened patch reviewer to compare diff headers with actual file markers.
- `65d9e8fa2f8645004e7813165ded7fb12af008c4` — added regression test proving mismatched file markers are blocked; code-worker tests and deployment passed.

Older secure-chat integration commits are documented in Git history; inspect `src/chat/secureBridge.ts`, `worker/index.js`, and the Manager/runtime workflows for the current source of truth rather than relying on commit summaries alone.

## 7. Next steps — do these in order

### Priority 1 — close the active bounded-worker run
1. Check [run 40083434881](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/40083434881), last observed in the model execution step.
2. Confirm whether execution finishes, times out, or fails. If it fails, inspect the job logs and redacted artifact before changing code.
3. Verify that independent patch review and artifact upload ran; inspect `worker-result.json`, `patch-review.json`, changed paths, and the patch itself.
4. This worker is now manual-dispatch only; ordinary pushes should not start the model-heavy Ollama/Qwen job. To run it, use Actions → Bounded AI Worker (Patch Only) → Run workflow and choose a JSON task in `tasks/`.
5. Do not accept or apply a patch solely because the workflow job is green.

### Priority 2 — fix the demo task/source mismatch
1. Inspect the real homepage at `https://jpmangaatlis.online/` and the target repository's current `index.html`.
2. Rewrite `tasks/demo-bounded-code-proposal.json` so its objective refers only to evidence that really exists in that repository.
3. Keep the allowlist narrow, and preserve proposal-only behavior.
4. Run the worker and independent reviewer again; require Captain review. Do not merge/deploy the generated patch automatically.

### Priority 3 — configure and verify direct GitHub-only Manager Chat
1. Create a fine-grained token owned by `WebControlerAgent`, limited to this repository, with Issues read/write only.
2. Open the deployed AIWCU website, paste the token into Manager Chat, and click **Connect GitHub**.
3. Send a harmless Manager AI instruction. The page should create a `[Manager AI]` issue automatically without a manual issue submission.
4. Confirm `manager-ai.yml` starts, then verify the final Manager AI comment and any follow-up `agent-command.yml` runtime result appears in the website chat.
5. Check Actions logs for any API/CORS/auth/polling issue. Do not grant broad app permissions or add Cloudflare/Supabase. The current implementation is committed but not yet proven by a live end-to-end run.

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

- **Last updated:** 2026-10-24
- **Manager Chat scoped-token connection:** replaced the browser Device Flow approach after GitHub's device-code endpoint blocked cross-origin requests. The chat now accepts a fine-grained token limited to this repository with Issues read/write, verifies account/repository access, and keeps the token in memory only. Deployment and a real command/result round trip still need verification.
- **Worker API validation:** commits `0aceeedfd8069751ba615b39b857769b9bc8c73d` and `daee3b6c8057b9b2c40efcc1db70a9a2a1608476` return HTTP 400 for invalid JSON/runtime payloads and add tests for runtime validation, result polling, and invalid issue IDs. [Prior bridge test run 39098188620 — SUCCESS](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39098188620); latest run [39098198794](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39098198794) was running at the time of this update.
- **Secure bridge deployment prep:** added `worker/wrangler.toml` (commit `7d12a9725d6773c273de601ada64ca3ff9678868`) and CLI deployment/secrets instructions in `worker/README.md` (commit `2541f668a1a37b7ae2107bc3c3af88971d910098`).
- **Bridge safety tests:** added `worker/index.test.js` and wired it into the existing CI workflow (commit `9c3a3d501448b74d21cf1cf2bb0adbe9a2035701`); [run 39056193187 — SUCCESS](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39056193187), including Python worker tests and Node bridge tests.
- **Pages deployment for latest CI commit:** [run 39056193225](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39056193225) was queued at last check.
- **Bounded AI Worker:** [run 39055110977 — SUCCESS](https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/runs/39055110977); patch artifact and deterministic scope/risk review succeeded. The proposal changes only the homepage meta description and is `READY_FOR_CAPTAIN_REVIEW`; no source site was modified, and no automatic merge/deploy occurred.
- **Coding worker completion fix:** commit `9293251c70d2995e68c0c96d6fa193162a238da4`; bounded worker and Pages deployment both succeeded after this fix.
- **Manager Chat E2E:** scoped-token connection is implemented in source. After Pages deploys, create the minimum-permission fine-grained token and test one harmless command/result round trip. No Cloudflare Worker is required.
- **Next immediate action:** verify the Pages build, then connect using a token scoped only to this repo and test the issue → Manager comment → in-chat result flow. Never commit tokens or Gemini keys.
- **SEO note:** keep the Kingdom Raw canonical/live-domain mismatch as a separate Captain-reviewed task; do not apply the demo meta-description patch as a substitute for fixing canonical configuration.
