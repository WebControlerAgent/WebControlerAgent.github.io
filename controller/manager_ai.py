"""Protected Manager AI bridge for GitHub Actions."""
from __future__ import annotations

import json
import os
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
API = "https://generativelanguage.googleapis.com/v1beta/models/" + MODEL + ":generateContent"
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
    req = Request(
        API,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": key,
        },
    )

    last_error = None
    for attempt in range(3):
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
            if exc.code not in RETRYABLE_STATUS or attempt == 2:
                try:
                    detail = exc.read().decode("utf-8", errors="replace")
                except Exception:
                    detail = ""
                raise RuntimeError(f"Gemini API HTTP {exc.code}: {detail[:500]}") from exc
            time.sleep(2 ** attempt)
        except (TimeoutError, OSError) as exc:
            last_error = exc
            if attempt == 2:
                raise RuntimeError(f"Gemini API request failed: {exc}") from exc
            time.sleep(2 ** attempt)

    raise RuntimeError(f"Gemini API request failed: {last_error}")


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
