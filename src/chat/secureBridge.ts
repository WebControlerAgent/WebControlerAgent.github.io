export type BridgeConfig = { url: string; key: string };
export type BridgeSubmission = { issue: number; issueUrl: string; state: string };
export type BridgeResult = { issue: number; state: string; comments: { author: string; body: string; createdAt: string }[] };

async function call<T>(config: BridgeConfig, path: string, init: RequestInit = {}): Promise<T> {
  const base = config.url.trim().replace(/\/+$/, "");
  if (!/^https:\/\//i.test(base)) throw new Error("Bridge URL must start with https://");
  const response = await fetch(base + path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + config.key,
      ...(init.headers || {})
    }
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Bridge request failed (" + response.status + ")");
  return data as T;
}
export function submitManager(config: BridgeConfig, instruction: string) {
  return call<BridgeSubmission>(config, "/command", { method: "POST", body: JSON.stringify({ instruction }) });
}
export function submitRuntime(config: BridgeConfig, command: Record<string, unknown>) {
  return call<BridgeSubmission>(config, "/runtime", { method: "POST", body: JSON.stringify(command) });
}
export function readResult(config: BridgeConfig, issue: number) {
  return call<BridgeResult>(config, "/result?issue=" + encodeURIComponent(String(issue)));
}
