# Studio Chat — GitHub-only scoped-token connection

- `managerReply()` remains a local fallback for agent/status responses when GitHub is not connected.
- The chat accepts a **fine-grained personal access token** and verifies the GitHub account is `WebControlerAgent` plus access to this exact repository before enabling commands.
- Create the token with resource owner `WebControlerAgent`, repository access limited to `WebControlerAgent.github.io`, and **Issues: Read and write**. Do not grant Contents, Actions, Administration, or access to other repositories.
- The browser keeps the token only in React component memory. It is not written to localStorage, sessionStorage, source files, or logs; reloading or disconnecting clears it.
- Security limitation: a token used by a public browser app is accessible to that page's JavaScript and potentially malicious browser extensions or an XSS vulnerability. This is less secure than a server-side credential. Never paste a classic broad-scope token or a token that can access other repositories.
- The token is used to create a `[Manager AI]` issue and read issue comments. The issue-opened workflow performs Manager AI using the Actions-side `GEMINI_API_KEY`; that key must never be placed in the website.
- Workflow results are polled from issue comments and shown in chat. A pending comment is not considered a final result; the UI waits for a non-pending Manager/runtime response.
- If connection fails, check that the token belongs to `WebControlerAgent`, has not expired, and has Issues read/write on this repository.
- `secureBridge.ts` and `worker/index.js` are legacy optional bridge code, not used by the current chat.
- End-to-end testing is still required after the next Pages deployment; a successful source update alone does not prove workflow completion.
