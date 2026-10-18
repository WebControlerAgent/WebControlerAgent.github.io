# Studio Chat — GitHub-only device authorization

- `managerReply()` remains a local fallback for agent/status responses when GitHub is not connected.
- `githubDeviceFlow.ts` implements GitHub App Device Flow, checks the signed-in account is exactly `WebControlerAgent`, creates a `[Manager AI]` issue, and reads its comments.
- The browser holds the access token only in React component memory. It is not written to localStorage, sessionStorage, source files, or logs; reload/disconnect clears it.
- Configure a GitHub App owned by the repository owner, enable Device Flow, install it only on `WebControlerAgent/WebControlerAgent.github.io`, and grant only Issues read/write. The issue-opened workflow performs Manager AI using the Actions-side `GEMINI_API_KEY`; do not grant the app Contents or Actions permissions.
- The app Client ID is public configuration, not a secret. Do not use a broad OAuth App with account-wide `repo` scope.
- Workflow results are polled from issue comments and shown in chat. A pending comment is not considered a final result; the UI waits for a non-pending Manager/runtime response.
- If device authorization or issue creation fails, verify Device Flow is enabled, the app is installed on this exact repo, the permission is present, and the current GitHub account is `WebControlerAgent`.
- `secureBridge.ts` and `worker/index.js` are legacy optional bridge code, not used by the current chat.
- Live end-to-end testing is still required after the next Pages deployment; a successful TypeScript build alone does not prove OAuth/API CORS or workflow completion.
