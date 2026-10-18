# Studio Chat — GitHub-only mode

- `managerReply()` provides local status/agent responses and prepares explicit runtime commands or natural-language Manager AI requests.
- Runtime status is read from the published `public/status.json` artifact.
- Manager Chat builds prefilled GitHub Issue links: `[Manager AI]` for natural-language planning and `[Agent Runtime]` for supported runtime state commands.
- The user must open the link and click **Submit new issue** on GitHub. This is intentional: GitHub Pages is static and must not contain a GitHub token, Gemini key, or chat secret.
- `.github/workflows/manager-ai.yml` and `.github/workflows/agent-command.yml` accept only issues matching their title prefixes and repository authorization checks.
- Results are posted as comments on the GitHub Issue thread. The public page does not poll the issue because private issue access requires authentication.
- `secureBridge.ts` and `worker/index.js` are legacy optional bridge code; they are not part of the current GitHub-only chat path.
- Submitting an issue is not proof of completion. Verify the Actions run and its result comments/artifacts.
