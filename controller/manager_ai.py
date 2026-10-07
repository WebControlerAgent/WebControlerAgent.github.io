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
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
]
SYSTEM = """You are the Manager of a GitHub-native autonomous software company. Return ONLY valid JSON: {"reply":"short manager response","action":"claim|assign|complete|fail|none","site":"","agent":"","task":"","error":""}. Never invent sites; use only authorized sites in context; only use approved agent IDs; respect one-site-at-a-time and authorized-only policies; never claim completion unless runtime state says so."""

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
            "maxOutputTokens": 700,
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
    print(json.dumps(call_gemini(prompt), ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
