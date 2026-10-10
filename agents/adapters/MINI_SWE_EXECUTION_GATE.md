# mini-SWE-agent execution gate

## Current stage: preflight only

The workflow pins mini-SWE-agent to v2.4.6, verifies that the `mini` CLI is installed, and emits a JSON evidence artifact. It does **not** send a task to a model or execute model-generated shell commands.

## Why repairs are not enabled yet

mini-SWE-agent uses a shell tool. If a provider API key is placed in the same process environment, model-generated shell commands may be able to read or exfiltrate it. A temporary GitHub runner and read-only GitHub token do not by themselves solve this credential exposure problem.

Before real repairs are enabled, provide a sandbox architecture where:
- the agent shell has no GitHub token, deployment credential, or provider API key;
- model requests pass through a separate authenticated proxy that keeps provider credentials outside the shell;
- filesystem access is limited to a disposable worktree and an explicit path allowlist;
- network egress is restricted to the proxy and approved package sources;
- the output is a patch artifact only, never an automatic merge or deployment;
- an independent checker runs tests and a human approves any merge.

## Patch gate

The preflight helper can inspect an existing unified diff. It blocks absolute/traversal paths, workflow changes, environment/credential filenames, and files outside the approved prefixes. Passing this simple path check is not code approval; a separate security review and test run remain required.

## Run

Open **Actions → mini-SWE-agent Preflight and Patch Gate → Run workflow**. The job uses read-only repository permissions and does not require an LLM secret. It should be treated as a preflight, not as a working autonomous repair agent.
