"""Protected Manager AI bridge for GitHub Actions."""
from __future__ import annotations

import json
import os
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
FALLBACK_MODELS = [
    MODEL,
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
]
SYSTEM = """You are the user's conversational AI Manager inside a GitHub-only Agent Workspace. The user may speak naturally in English, Urdu, or Roman Urdu; reply in the same language/style, usually concise Roman Urdu when the user uses it. You may answer questions, explain plans, ask one essential clarification, summarize status, and help break work into steps like a helpful assistant. Return ONLY valid JSON with exactly these keys: {"reply":"natural conversational answer","action":"claim|assign|complete|fail|none","site":"","agent":"","task":"","error":""}. Treat the section labeled LATEST USER INSTRUCTION as the only current request. Earlier conversation is context only; do not repeat or execute old commands unless the latest request clearly continues them. For normal questions, greetings, planning, and requests that the current runtime cannot actually execute, use action "none" and answer honestly. Never pretend you edited files, ran tests, browsed a target, fixed a site, deployed code, or completed work unless runtime evidence in the supplied context proves it. The current runtime can perform a bounded site-claim pipeline and record validated state transitions; an "assign" action only records an assignment and does NOT start a worker. The coding worker is a separate bounded patch-proposal workflow; it does not write to the target repository, merge, or deploy. If the user asks for code changes, explain the real next safe step rather than claiming execution. Never invent sites: use only enabled and authorized sites in context. Use only approved agent IDs. Respect the one-site-at-a-time lock and authorized-only policy. Keep reply helpful and specific, usually under 1200 characters."""

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def call_gemini(prompt):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.2,
            "maxOutputTokens": 1200,
        },
    }
    body = json.dumps(payload).encode("utf-8")
    last_error = None

    for model_index, model in enumerate(dict.fromkeys(FALLBACK_MODELS)):
        api = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent"
        req = Request(
            api,
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": key,
            },
        )

        for attempt in range(2):
            try:
                with urlopen(req, timeout=45) as response:
                    data = json.loads(response.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                result = json.loads(text)
                if result.get("action") not in {"claim", "assign", "complete", "fail", "none"}:
                    raise ValueError("Invalid AI action")
                return result
            except HTTPError as exc:
                last_error = exc
                if exc.code not in RETRYABLE_STATUS:
                    try:
                        detail = exc.read().decode("utf-8", errors="replace")
                    except Exception:
                        detail = ""
                    raise RuntimeError(
                        f"Gemini API HTTP {exc.code} on {model}: {detail[:500]}"
                    ) from exc
                if attempt == 1:
                    break
                time.sleep(2)
            except (TimeoutError, OSError) as exc:
                last_error = exc
                if attempt == 1:
                    break
                time.sleep(2)

    if isinstance(last_error, HTTPError):
        try:
            detail = last_error.read().decode("utf-8", errors="replace")
        except Exception:
            detail = ""
        raise RuntimeError(
            f"All Gemini models unavailable. Last HTTP {last_error.code}: {detail[:500]}"
        ) from last_error
    raise RuntimeError(f"All Gemini model requests failed: {last_error}")


def validate_plan(result, sites_data, runtime_state):
    """Fail closed if model output requests an unknown site or invalid state transition."""
    try:
        from .agent_runtime import AGENTS
    except ImportError:
        from agent_runtime import AGENTS

    if not isinstance(result, dict):
        return {"reply": "Manager response was not a valid plan; no action was dispatched.", "action": "none"}
    action = result.get("action")
    if action not in {"claim", "assign", "complete", "fail", "none"}:
        return {"reply": "Manager returned an unsupported action; no action was dispatched.", "action": "none"}
    if action == "none":
        return {
            "reply": str(result.get("reply", "No runtime action needed."))[:1000],
            "action": "none",
        }

    active = runtime_state.get("active_site") if isinstance(runtime_state, dict) else None
    authorized = {
        str(site.get("id"))
        for site in sites_data.get("sites", [])
        if isinstance(site, dict) and site.get("enabled") is True and site.get("authorized") is True and site.get("id")
    }
    site = str(result.get("site") or "").strip()
    agent = str(result.get("agent") or "").strip()
    task = str(result.get("task") or "").strip()

    if action == "claim":
        if active:
            return {"reply": "A site is already active; I will not start a second site.", "action": "none"}
        if site not in authorized:
            if not site and len(authorized) == 1:
                site = next(iter(authorized))
            else:
                return {"reply": "The requested site is not in the enabled, authorized site list; no action was dispatched.", "action": "none"}
        return {**result, "site": site, "reply": str(result.get("reply", "Starting the authorized site pipeline."))[:1000]}

    if not active:
        return {"reply": "No active site exists for that runtime action; no action was dispatched.", "action": "none"}
    active_id = str(active.get("id") or "")
    if site and site != active_id:
        return {"reply": "The requested site does not match the active site; no action was dispatched.", "action": "none"}
    if action == "assign":
        if agent not in AGENTS or not task or len(task) > 500:
            return {"reply": "The agent or task was invalid; no action was dispatched.", "action": "none"}
        return {**result, "site": active_id, "agent": agent, "task": task, "reply": str(result.get("reply", "Task assignment prepared."))[:1000]}
    if action in {"complete", "fail"}:
        return {**result, "site": active_id, "reply": str(result.get("reply", "Runtime state transition prepared."))[:1000]}
    return {"reply": "Manager plan was rejected; no action was dispatched.", "action": "none"}


def main():
    instruction = " ".join(sys.argv[1:]).strip()
    if not instruction or len(instruction) > 4000:
        raise ValueError("instruction must be 1-4000 chars")

    state = json.load(open("controller/agent_state.json", encoding="utf-8"))
    sites = json.load(open("controller/sites.json", encoding="utf-8"))
    prompt = json.dumps(
        {
            "instruction": instruction,
            "runtime_state": state,
            "authorized_sites": sites,
        },
        ensure_ascii=False,
    )
    result = call_gemini(prompt)
    result = validate_plan(result, sites, state)
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
