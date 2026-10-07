# Controller engine

This controller is the server-side worker for the Web Controller Agent.

It intentionally supports **authorized sources only**. A source must be explicitly enabled in
`controller/config.json`, and every source must have an explicit route to a target repository.

## Supported source

`json_api` reads a JSON document from an API/feed that you are authorized to process. It does
not bypass login walls, anti-bot systems, paywalls, DRM, or access controls.

## Target

The GitHub target adapter writes a small JSON manifest into the configured target repository.
The target repository is authenticated with `CROSS_REPO_TOKEN` (Actions secret) and never from
frontend JavaScript.

## State

- `controller/state.json` stores the last-seen item IDs.
- `public/status.json` is the dashboard status artifact.
- Failed jobs are retried up to the configured limit.

For real publishing of files owned by you, add a dedicated target adapter after the manifest
flow is verified.
