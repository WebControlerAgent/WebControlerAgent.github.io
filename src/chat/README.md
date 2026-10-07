# Studio Chat

The chat surface uses an adapter-based UI.

- managerReply() is the local fallback and never pretends to be an LLM.
- Runtime state comes from public/status.json.
- A future AgentRuntimeAdapter can replace the local fallback with gh-aw or another approved engine without changing the 3D office UI.
- Privileged GitHub writes stay on GitHub Actions/server-side; repository tokens never go in the browser.
