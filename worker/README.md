# AIWCU secure chat bridge (free-tier setup)

This bridge keeps the GitHub token on Cloudflare, not in the public GitHub Pages bundle.

## 1. Deploy the Worker
1. Create a Cloudflare account and create a Worker named `aiwcu-chat-bridge`.
2. Paste the code from `worker/index.js` and deploy.
3. In Worker **Settings → Variables and Secrets**, add:
   - Secret `GITHUB_TOKEN`: a fine-grained token scoped only to `WebControlerAgent/WebControlerAgent.github.io`, with **Issues: Read and write**.
   - Secret `AIWCU_CHAT_KEY`: a long random private key. Do not commit it to GitHub.
   - Variable `ALLOWED_ORIGIN`: the exact public website origin (for example `https://webcontroleragent.github.io`; use the actual deployed origin).
4. Do not share the private key. Rotate it if exposed.

## 2. Current boundary
The Worker creates a `[Manager AI]` issue and can read the workflow's reply comments. It does **not** put the Gemini secret in the browser. The existing Manager workflow currently comments when the AI plan is ready; the separate runtime worker may continue afterward. Full worker-completion correlation into the same chat is a subsequent step.

## 3. Frontend connection
The public page must be configured with the deployed Worker URL and the private chat key entered by the authorized operator at runtime. Never add either private key to `VITE_*` variables or commit it into `src/`.
