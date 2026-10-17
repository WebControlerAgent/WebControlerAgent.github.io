import test from "node:test";
import assert from "node:assert/strict";
import worker from "./index.js";

const origin = "https://site.example";
const env = {
  GITHUB_TOKEN: "test-github-token",
  AIWCU_CHAT_KEY: "test-chat-key",
  ALLOWED_ORIGIN: origin,
};

function makeRequest(path, { method = "POST", requestOrigin = origin, key = "test-chat-key", body } = {}) {
  const headers = { Origin: requestOrigin };
  if (key !== null) headers.Authorization = "Bearer " + key;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  return new Request("https://bridge.example" + path, {
    method,
    headers,
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
}

test("preflight permits the configured origin", async () => {
  const response = await worker.fetch(makeRequest("/command", { method: "OPTIONS" }), env);
  assert.equal(response.status, 204);
  assert.equal(response.headers.get("Access-Control-Allow-Origin"), origin);
});

test("rejects a non-allowlisted origin", async () => {
  const response = await worker.fetch(
    makeRequest("/command", { requestOrigin: "https://attacker.example", body: { instruction: "hello" } }),
    env,
  );
  assert.equal(response.status, 403);
});

test("fails closed when bridge secrets are missing", async () => {
  const response = await worker.fetch(makeRequest("/command", { body: { instruction: "hello" } }), {
    ALLOWED_ORIGIN: origin,
  });
  assert.equal(response.status, 503);
});

test("rejects an incorrect chat key", async () => {
  const response = await worker.fetch(
    makeRequest("/command", { key: "wrong-key", body: { instruction: "hello" } }),
    env,
  );
  assert.equal(response.status, 401);
});

test("rejects empty Manager instructions without calling GitHub", async () => {
  const response = await worker.fetch(makeRequest("/command", { body: { instruction: "   " } }), env);
  assert.equal(response.status, 400);
});

test("creates a Manager issue only after origin and key checks", async () => {
  const originalFetch = globalThis.fetch;
  let capturedUrl = "";
  let capturedInit;
  globalThis.fetch = async (input, init) => {
    capturedUrl = String(input);
    capturedInit = init;
    return new Response(JSON.stringify({
      number: 123,
      html_url: "https://github.com/WebControlerAgent/WebControlerAgent.github.io/issues/123",
    }), { status: 201, headers: { "Content-Type": "application/json" } });
  };
  try {
    const response = await worker.fetch(
      makeRequest("/command", { body: { instruction: "Please summarize current worker status." } }),
      env,
    );
    assert.equal(response.status, 202);
    assert.equal(capturedUrl, "https://api.github.com/repos/WebControlerAgent/WebControlerAgent.github.io/issues");
    assert.equal(capturedInit.method, "POST");
    assert.match(JSON.parse(capturedInit.body).title, /^\[Manager AI\]/);
    const result = await response.json();
    assert.equal(result.issue, 123);
    assert.equal(result.state, "submitted");
  } finally {
    globalThis.fetch = originalFetch;
  }
});
