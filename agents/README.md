# Agent Registry

The Studio uses GitHub Agentic Workflows as an optional reasoning layer and deterministic GitHub Actions/scripts as the execution layer. This follows the upstream gh-aw model: agents handle reasoning and interpretation while builds, tests, deployments and reproducible operations remain deterministic.

Architectural references:
- github/gh-aw — agentic workflows compiled into GitHub Actions.
- eloylp/agents — self-hosted multi-agent scheduling, skills, memory and event-driven dispatch.

We adapt useful patterns rather than copying third-party projects wholesale.

## Agent contract

Each agent receives the active site, current state, task, previous output, allowed tools and retry count.

Each agent returns status, summary, artifacts, next_agent and error when applicable.

The Manager is the coordinator. Only one site can be active at once. A failed site blocks the next site until Bug Hunter, Bug Solver and QA complete the repair cycle.

## AI engine

An open-ended AI worker requires an inference engine. gh-aw supports multiple engines, so the Studio keeps the agent contract independent of the engine. Deterministic operations continue without an AI engine, and an engine can be attached later without redesigning the runtime.
