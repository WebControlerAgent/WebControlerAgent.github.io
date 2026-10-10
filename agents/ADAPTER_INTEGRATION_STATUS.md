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