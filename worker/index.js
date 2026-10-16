/**
 * AIWCU secure command bridge for Cloudflare Workers.
 * Configure secrets: GITHUB_TOKEN (repo-scoped token with Issues read/write),
 * AIWCU_CHAT_KEY (random private key), and vars ALLOWED_ORIGIN (site origin).
 * Deploy this Worker, then set the URL in the site's runtime settings.
 */
const REPO = "WebControlerAgent/WebControlerAgent.github.io";
const API = "https://api.github.com";
function bodyCommand(value) {
  const allowed = new Set(["claim", "assign", "verify", "complete", "fail"]);
  if (!value || !allowed.has(value.action)) throw new Error("Unsupported runtime action");
  const out = { action: value.action };
  for (const key of ["site", "agent", "task", "error"]) {
    if (value[key] != null) {
      const v = String(value[key]).trim();
      if (v.length > 500) throw new Error(key + " is too long");
      out[key] = v;
    }
  }
  if (value.passed != null) out.passed = Boolean(value.passed);
  return out;
}

function cors(origin, env) {
  const allowed = (env.ALLOWED_ORIGIN || "").split(",").map(x => x.trim()).filter(Boolean);
  return {
    "Access-Control-Allow-Origin": allowed.includes(origin) ? origin : "null",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Vary": "Origin",
    "Content-Type": "application/json; charset=utf-8"
  };
}
function json(data, status, headers) {
  return new Response(JSON.stringify(data), { status, headers });
}
async function gh(path, env, init = {}) {
  const response = await fetch(API + path, {
    ...init,
    headers: {
      "Accept": "application/vnd.github+json",
      "Authorization": "Bearer " + env.GITHUB_TOKEN,
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "AIWCU-secure-bridge",
      ...(init.headers || {})
    }
  });
  const body = await response.text();
  if (!response.ok) throw new Error("GitHub API " + response.status + ": " + body.slice(0, 300));
  return body ? JSON.parse(body) : {};
}
export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    const headers = cors(origin, env);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers });
    if (!headers["Access-Control-Allow-Origin"] || headers["Access-Control-Allow-Origin"] === "null") {
      return json({ error: "Origin not allowed" }, 403, headers);
    }
    if (!env.GITHUB_TOKEN || !env.AIWCU_CHAT_KEY) return json({ error: "Bridge secrets are not configured" }, 503, headers);
    if (request.headers.get("Authorization") !== "Bearer " + env.AIWCU_CHAT_KEY) {
      return json({ error: "Unauthorized. Enter the private AIWCU chat key." }, 401, headers);
    }
    const url = new URL(request.url);
    try {
      if (request.method === "POST" && url.pathname === "/command") {
        const body = await request.json();
        const instruction = String(body.instruction || "").trim();
        if (!instruction || instruction.length > 4000) return json({ error: "Instruction must be 1–4000 characters." }, 400, headers);
        const issue = await gh("/repos/" + REPO + "/issues", env, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: "[Manager AI] " + instruction.replace(/\s+/g, " ").slice(0, 70),
            body: "Submitted from the authenticated AIWCU Manager Chat.\n\n" + instruction
          })
        });
        return json({ issue: issue.number, issueUrl: issue.html_url, state: "submitted" }, 202, headers);
      }
      if (request.method === "POST" && url.pathname === "/runtime") {
        const command = bodyCommand(await request.json());
        const issue = await gh("/repos/" + REPO + "/issues", env, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title: "[Agent Runtime] " + command.action,
            body: "Submitted from the authenticated AIWCU Manager Chat.\\n\\n<!-- agent-runtime-command\\n" + JSON.stringify(command, null, 2) + "\\n-->"
          })
        });
        return json({ issue: issue.number, issueUrl: issue.html_url, state: "submitted" }, 202, headers);
      }
      if (request.method === "GET" && url.pathname === "/result") {
        const issue = Number(url.searchParams.get("issue"));
        if (!Number.isSafeInteger(issue) || issue < 1) return json({ error: "Valid issue number required." }, 400, headers);
        const data = await gh("/repos/" + REPO + "/issues/" + issue + "/comments?per_page=30", env);
        const comments = data.map(c => ({
          author: c.user?.login || "GitHub",
          body: String(c.body || "").slice(0, 4000),
          createdAt: c.created_at
        }));
        const issueData = await gh("/repos/" + REPO + "/issues/" + issue, env);
        return json({ issue, state: issueData.state, comments }, 200, headers);
      }
      return json({ error: "Not found" }, 404, headers);
    } catch (error) {
      return json({ error: String(error?.message || error).slice(0, 500) }, 502, headers);
    }
  }
};
