# AIWCU secure chat bridge (free-tier setup)

The website's Manager Chat uses this bridge to submit authenticated commands to GitHub Actions. GitHub Pages must never contain the GitHub token, chat key, or Gemini key.

## Deploy from the repository (recommended)

1. Create/sign in to a free Cloudflare account and install a current Node.js LTS release locally.
2. Open `worker/wrangler.toml` and set `ALLOWED_ORIGIN` to the exact origin shown in the live website's browser address bar, with no trailing slash. Examples: `https://webcontroleragent.github.io` or your verified custom domain. Do not leave it blank.
3. From the repository root, authenticate Wrangler and deploy:
   ```sh
   npx wrangler login
   npx wrangler deploy --config worker/wrangler.toml
   ```
4. Add secrets interactively. Do not paste their values into source files or chat:
   ```sh
   npx wrangler secret put GITHUB_TOKEN --config worker/wrangler.toml
   npx wrangler secret put AIWCU_CHAT_KEY --config worker/wrangler.toml
   ```
   - `GITHUB_TOKEN`: fine-grained token scoped only to `WebControlerAgent/WebControlerAgent.github.io`, with **Issues: Read and write** permissions. The token's owner must be authorized to open issues in this repository so issue-triggered workflows accept requests.
   - `AIWCU_CHAT_KEY`: a long, randomly generated private key. Keep it private; it is entered into the chat UI only for the current page session.
5. If you change `ALLOWED_ORIGIN`, redeploy so the Worker uses the new value:
   ```sh
   npx wrangler deploy --config worker/wrangler.toml
   ```
6. Wrangler prints the deployed `workers.dev` URL. Enter that URL and the same `AIWCU_CHAT_KEY` in the website's bridge prompt.

The repository now includes `worker/wrangler.toml` so the Worker name and entry point are repeatable; it does not contain secrets. The Cloudflare account login, secrets, and deployment still require the site owner to authorize them.

## Dashboard alternative

1. Create a Worker named `aiwcu-chat-bridge` and paste `worker/index.js` into its editor.
2. In **Settings → Variables and Secrets**, set the same two secrets and the exact `ALLOWED_ORIGIN` value above.
3. Deploy and use the generated Worker URL in the website's bridge prompt.

## Verify the end-to-end flow

1. Confirm the latest GitHub Pages deployment succeeded.
2. Open the live site and configure the Worker URL and private chat key when prompted.
3. Send a harmless Manager instruction. Confirm it creates a `[Manager AI]` GitHub issue, the Manager workflow runs, and the resulting comment appears in the chat.
4. Test a runtime command separately and confirm its result comment. If the browser stops polling before a long job finishes, inspect the related GitHub Actions run and issue comments.

## Honest execution boundary

- Manager issues return the Manager workflow's planning response.
- Runtime issues return the runtime workflow's completion/failure comment if it arrives while the chat is polling. Longer jobs may finish after polling stops; check GitHub Actions in that case.
- The Gemini API key remains only in GitHub Actions Secrets. Never put it in Worker frontend settings or any `VITE_*` variable.
- Never paste either secret into an issue, commit, screenshot, or chat message. Rotate secrets if exposed.
