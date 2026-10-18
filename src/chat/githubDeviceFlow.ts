const API = "https://api.github.com";
const REPO = "WebControlerAgent/WebControlerAgent.github.io";
const OWNER_LOGIN = "WebControlerAgent";

async function jsonResponse(response: Response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.message || data.error_description || data.error || `GitHub request failed (${response.status})`);
  return data;
}

export async function verifyGitHubToken(token: string): Promise<string> {
  const clean = token.trim();
  if (!clean) throw new Error("Fine-grained GitHub token paste karo.");
  const user = await githubRequest("/user", clean);
  if (String(user.login || "").toLowerCase() !== OWNER_LOGIN.toLowerCase()) {
    throw new Error("Is control panel ke liye GitHub account WebControlerAgent hona chahiye. Token kisi aur account ka hai.");
  }
  // Confirm this token can access the one intended repository before enabling chat.
  await githubRequest("/repos/" + REPO, clean);
  return clean;
}

async function githubRequest(path: string, token: string, init: RequestInit = {}) {
  const response = await fetch(API + path, {
    ...init,
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: "Bearer " + token,
      "X-GitHub-Api-Version": "2022-11-28",
      "Content-Type": "application/json",
      ...(init.headers || {})
    }
  });
  return jsonResponse(response);
}

export async function createManagerRequest(token: string, instruction: string, siteName: string, siteId: string, conversationContext = "") {
  const body = [
    "Website Manager Chat request (GitHub-only).",
    "Active site: " + siteName + " (" + siteId + ")",
    "",
    "Recent conversation context (background only; do not repeat or execute old requests unless the latest instruction explicitly continues them):",
    conversationContext.trim() || "(no previous conversation)",
    "",
    "LATEST USER INSTRUCTION — this is the only request to answer or act on now:",
    instruction.trim()
  ].join("\n");
  return githubRequest("/repos/" + REPO + "/issues", token, {
    method: "POST",
    body: JSON.stringify({
      title: (/\bseo\b|search engine optimization|sitemap|robots\.txt|meta description|canonical|indexing issue/i.test(instruction) ? "[SEO Audit] " : "[Manager AI] ") + instruction.trim().replace(/\s+/g, " ").slice(0, 70),
      body
    })
  });
}

export async function readManagerComments(token: string, issueNumber: number) {
  return githubRequest("/repos/" + REPO + "/issues/" + issueNumber + "/comments?per_page=100", token);
}
