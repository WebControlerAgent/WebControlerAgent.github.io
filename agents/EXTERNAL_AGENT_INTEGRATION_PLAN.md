# External agent integration plan

This file is a research result, not a claim that third-party workers have been installed or executed.

## Recommended first wave

1. **Playwright** for repeatable UI smoke tests. It is the most reliable first addition because basic browser tests do not need an LLM API key.
2. **mini-swe-agent** for a single sandboxed code-repair task. The result must include a patch, test output and a QA decision.
3. **browser-use** for limited research and browser-driven checks. Keep the first use read-only and save evidence.
4. **dannwaneri/seo-agent** for read-only SEO reports after API secrets and usage limits are configured.

## Orchestration choice

AIWCU already has a Manager/Captain/team/task contract. Do not add CrewAI and LangGraph together at the start. Both are orchestration frameworks, not plug-and-play agents. First build a small adapter interface around the existing task/result schema; evaluate one framework only if the current deterministic Python workflow becomes insufficient.

## Required adapter contract

Every external worker should receive a task ID, authorized site, bounded objective, constraints and acceptance criteria. It must return a structured result with state, summary, evidence, artifact paths and next action. A worker must not mark its task complete without evidence.

## GitHub Actions deployment reality

GitHub Pages hosts the static console; it cannot keep agents running in the background. Worker jobs must execute on GitHub Actions or another trusted runtime and then publish state/results back to the repository. GitHub-hosted runners are ephemeral, not always-on. API keys must be configured as repository Actions secrets and never placed in frontend code, JSON inventory, logs or committed files.

## Candidate catalog

See [external_integrations.json](./external_integrations.json) for repository links, suggested captain mappings, requirements, limitations and current status.
