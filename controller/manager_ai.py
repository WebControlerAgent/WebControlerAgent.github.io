"""Protected Manager AI bridge for GitHub Actions."""
from __future__ import annotations
import json, os, sys
from urllib.request import Request, urlopen
MODEL=os.getenv("GEMINI_MODEL","gemini-3.8-flash")
API="https://generativelanguage.googleapis.com/v1beta/models/"+MODEL+":generateContent"
SYSTEM="""You are the Manager of a GitHub-native autonomous software company. Return ONLY valid JSON: {"reply":"short manager response","action":"claim|assign|complete|fail|none","site":"","agent":"","task":"","error":""}. Never invent sites; use only authorized sites in context; only use approved agent IDs; respect one-site-at-a-time and authorized-only policies; never claim completion unless runtime state says so."""
def call_gemini(prompt):
    key=os.environ.get("GEMINI_API_KEY","").strip()
    if not key: raise RuntimeError("GEMINI_API_KEY is not configured")
    payload={"system_instruction":{"parts":[{"text":SYSTEM}]},"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"response_mime_type":"application/json","temperature":0.2,"maxOutputTokens":700}}
    req=Request(API,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json","x-goog-api-key":key})
    with urlopen(req,timeout=45) as r: data=json.loads(r.read().decode())
    result=json.loads(data["candidates"][0]["content"]["parts"][0]["text"])
    if result.get("action") not in {"claim","assign","complete","fail","none"}: raise ValueError("Invalid AI action")
    return result
def main():
    instruction=" ".join(sys.argv[1:]).strip()
    if not instruction or len(instruction)>4000: raise ValueError("instruction must be 1-4000 chars")
    state=json.load(open("controller/agent_state.json",encoding="utf-8"))
    sites=json.load(open("controller/sites.json",encoding="utf-8"))
    prompt=json.dumps({"instruction":instruction,"runtime_state":state,"authorized_sites":sites},ensure_ascii=False)
    print(json.dumps(call_gemini(prompt),ensure_ascii=False,separators=(",",":")))
if __name__=="__main__": main()