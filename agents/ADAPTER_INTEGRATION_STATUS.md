# External worker adapters — safe integration contract

This contract is staged. An upstream agent is not marked connected until its command runs in CI and returns evidence.

## First integration: Playwright

The repository now has a Playwright smoke-test suite and a dedicated GitHub Actions workflow. Playwright is deterministic QA tooling, not an LLM agent. It provides test evidence to the QA Captain/checker.

## Next adapters

- **mini-swe-agent:** install a pinned version in a separate job only after a model provider secret and disposable sandbox are configured. Give it no deploy token and no repository write token. Return patch/artifact; a separate checker must run tests before merge.
- **browser-use:** Python >= 3.11, Browser Use package, and supported model credential. Begin with a bounded, read-only task. Allowlist destinations and set a timeout.
- **seo-agent:** optional and read-only until dependencies, license, data handling, API needs and spend limits are reviewed. No auto-publish by default.
- **LangGraph/CrewAI:** choose at most one later if the current dispatcher/task contract needs a real orchestration framework.

## Required result contract

Every adapter must return JSON fields: task_id, agent_id, state, summary, evidence, artifacts, changed_files, next_action. Missing evidence means the task cannot be marked completed.

## Secrets and permissions

Provider credentials belong in GitHub Actions Secrets. Never add keys to frontend bundles, committed JSON, logs or screenshots. Default to read-only contents: read. Write-capable tasks require an isolated branch, bounded allowed paths, independent checker and explicit approval before merge/deploy.

## Hosting

GitHub Pages serves the UI only. Run jobs in GitHub Actions or a trusted external runtime; Actions runners are ephemeral, not always-on.

## mini-SWE-agent preflight added

A manual workflow pins mini-SWE-agent v2.4.6, checks CLI availability, and uploads a JSON evidence artifact. Model-driven shell execution remains deliberately disabled until a sandboxed model proxy keeps provider credentials outside the agent shell. See `agents/adapters/MINI_SWE_EXECUTION_GATE.md`.

## Proposal-only model runtime

- `controller/model_worker_runtime.py` makes two Gemini `generateContent` API calls: one for a bounded JSON proposal and a second for independent review.
- The model has no tools; model output is never executed, applied, pushed, merged, or deployed. The output is an artifact for Captain review only.
- `.github/workflows/proposal-worker-runtime.yml` is manually triggered, uses read-only repository permissions, checks out without persisted credentials, and uploads the result artifact.
- Configure `GEMINI_API_KEY` as a repository Actions Secret before manually running the workflow. An optional repository Actions variable `GEMINI_MODEL` can override the default `gemini-2.5-flash`. Model API calls may incur usage charges; the workflow is not triggered automatically.
- Unit tests cover authorized-repository checks, path allowlisting, traversal rejection, proposal size limits, and a missing-secret diagnostic. The runtime writes a JSON diagnostic report on configuration/runtime errors when the output path is writable, so the Actions artifact can help explain a failed run. A passing checker recommendation is still not a merge/deploy authorization.
