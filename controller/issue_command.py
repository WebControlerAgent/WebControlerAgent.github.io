"""Parse and validate a GitHub Issue Agent Runtime command."""
from __future__ import annotations
import json, os, re
ALLOWED={"claim","assign","verify","complete","fail"}
OWNER="WebControlerAgent"
def main():
    with open(os.environ["GITHUB_EVENT_PATH"],encoding="utf-8") as f: event=json.load(f)
    issue=event.get("issue",{})
    author=(issue.get("user") or {}).get("login","")
    if author.lower()!=OWNER.lower(): raise PermissionError("Issue author is not authorized")
    if not (issue.get("title") or "").startswith("[Agent Runtime]"): raise ValueError("Not an Agent Runtime issue")
    m=re.search(r"<!--\s*agent-runtime-command\s*(\{.*?\})\s*-->", issue.get("body",""), re.S)
    if not m: raise ValueError("Missing agent-runtime-command block")
    data=json.loads(m.group(1))
    if data.get("action") not in ALLOWED: raise ValueError("Invalid runtime action")
    result={"action":data["action"]}
    for key in ("site","agent","task","error"):
        if key in data and data[key] is not None:
            value=str(data[key]).strip()
            if len(value)>500: raise ValueError(key+" is too long")
            result[key]=value
    if "passed" in data: result["passed"]="true" if bool(data["passed"]) else "false"
    print(json.dumps(result,separators=(",",":")))
if __name__=="__main__": main()