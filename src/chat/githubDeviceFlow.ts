const API = "https://api.github.com";
const DEVICE_CODE_URL = "https://github.com/login/device/code";
const TOKEN_URL = "https://github.com/login/oauth/access_token";
const REPO = "WebControlerAgent/WebControlerAgent.github.io";
const OWNER_LOGIN = "WebControlerAgent";

export type DevicePrompt = { userCode: string; verificationUri: string; expiresIn: number };

async function jsonResponse(response: Response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.message || data.error_description || data.error || `GitHub request failed (${response.status})`);
  return data;
}

export async function authorizeGitHubApp(
  clientId: string,
  onPrompt: (prompt: DevicePrompt) => void,
  onStatus: (message: string) => void
): Promise<string> {
  if (!clientId.trim()) throw new Error("GitHub App Client ID missing hai.");
  const codeResponse = await fetch(DEVICE_CODE_URL, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ client_id: clientId.trim() })
  });
  const device = await jsonResponse(codeResponse);
  if (!device.device_code || !device.user_code || !device.verification_uri) {
    throw new Error(device.error_description || device.error || "GitHub device authorization code nahi mila.");
  }
  onPrompt({ userCode: device.user_code, verificationUri: device.verification_uri, expiresIn: Number(device.expires_in || 900) });
  let interval = Math.max(5, Number(device.interval || 5));
  const expiresAt = Date.now() + Number(device.expires_in || 900) * 1000;

  while (Date.now() < expiresAt) {
    await new Promise<void>(resolve => window.setTimeout(() => resolve(), interval * 1000));
    const response = await fetch(TOKEN_URL, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: clientId.trim(),
        device_code: device.device_code,
        grant_type: "urn:ietf:params:oauth:grant-type:device_code"
      })
    });
    const tokenData = await response.json().catch(() => ({}));
    if (tokenData.access_token) {
      const token = String(tokenData.access_token);
      const user = await githubRequest("/user", token);
      if (String(user.login || "").toLowerCase() !== OWNER_LOGIN.toLowerCase()) {
        throw new Error("Is AIWCU control panel ke liye GitHub account WebControlerAgent hona chahiye. Koi aur account authorize nahi hua.");
      }
      onStatus("GitHub account verified: " + user.login);
      return token;
    }
    if (tokenData.error === "authorization_pending") {
      onStatus("GitHub approval ka intezar hai…");
      continue;
    }
    if (tokenData.error === "slow_down") {
      interval = Math.max(interval + 5, Number(tokenData.interval || 0));
      continue;
    }
    if (tokenData.error === "access_denied") throw new Error("GitHub authorization cancel kar di gayi.");
    if (tokenData.error === "expired_token") throw new Error("Device code expire ho gaya. Dobara Connect dabao.");
    throw new Error(tokenData.error_description || tokenData.error || "GitHub authorization fail hui.");
  }
  throw new Error("Device code expire ho gaya. Dobara Connect dabao.");
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

export async function createManagerRequest(token: string, instruction: string, siteName: string, siteId: string) {
  const body = [
    "Website Manager Chat request (GitHub-only device authorization).",
    "Active site: " + siteName + " (" + siteId + ")",
    "",
    "User instruction:",
    instruction.trim()
  ].join("\n");
  return githubRequest("/repos/" + REPO + "/issues", token, {
    method: "POST",
    body: JSON.stringify({
      title: "[Manager AI] " + instruction.trim().replace(/\s+/g, " ").slice(0, 70),
      body
    })
  });
}

export async function readManagerComments(token: string, issueNumber: number) {
  return githubRequest("/repos/" + REPO + "/issues/" + issueNumber + "/comments?per_page=100", token);
}
