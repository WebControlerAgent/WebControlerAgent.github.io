# AIWCU secure chat bridge (free-tier setup)

The website's Manager Chat now has a client for this bridge. GitHub Pages cannot safely hold the GitHub token or Gemini key, so the bridge must be deployed separately.

## Deploy on Cloudflare Workers
1. Create a free Cloudflare account and a Worker named `aiwcu-chat-bridge`.
2. Paste the contents of `worker/index.js` into the Worker editor and deploy.
3. In **Settings → Variables and Secrets**, configure:
   - Secret `GITHUB_TOKEN`: a fine-grained token scoped only to `WebControlerAgent/WebControlerAgent.github.io`, with **Issues: Read and write** permissions.
   - Secret `AIWCU_CHAT_KEY`: a long random private key. Do not commit it to GitHub.
   - Variable `ALLOWED_ORIGIN`: the exact origin shown in the browser address bar for the live website, without a trailing slash (for example `https://webcontroleragent.github.io` only if that is the actual URL).
4. The GitHub token must belong to an account authorized to open issues in this repository, so the existing issue-triggered workflows accept the request.
5. Keep the private chat key private. Rotate both secrets if exposed.

## Use it from the site
1. Wait for the GitHub Pages deployment workflow to finish successfully after the frontend commit.
2. Open the site and send a command that needs real Manager AI or runtime work.
3. When prompted, enter the deployed Worker URL (for example `https://aiwcu-chat-bridge.<your-subdomain>.workers.dev`) and the `AIWCU_CHAT_KEY`. The chat keeps these in memory for the current page session; it does not write the key into the source code.
4. The bridge submits the request as a GitHub issue and polls the issue comments for the workflow response.

## Honest execution boundary
- Manager AI issues return the Manager workflow's planning response.
- Runtime issues return the runtime workflow's completion/failure comment if it arrives while the chat is polling. Longer jobs may finish after the chat stops polling; check GitHub Actions in that case.
- The Gemini API key remains only in GitHub Actions Secrets. Never place it in the Worker frontend settings or any `VITE_*` variable.
