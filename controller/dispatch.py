"""Apply one safe Agent Runtime command.

This file is deterministic. AI reasoning belongs in an agent adapter; this command layer only performs validated state transitions.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
STATE=ROOT/"controller"/"agent_state.json"
STATUS=ROOT/"public"/"status.json"
from agent_runtime import normalize, claim_site, assign, verify, complete_site, fail_site, AGENTS

def load(path, default):
    if not path.exists(): return default
    return json.loads(path.read_text(encoding="utf-8"))

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--action",required=True,choices=["claim","assign","verify","complete","fail"])
    p.add_argument("--site",default=""); p.add_argument("--agent",default="")
    p.add_argument("--task",default=""); p.add_argument("--passed",default="false"); p.add_argument("--error",default="")
    args=p.parse_args()
    state=normalize(load(STATE,None))
    if args.action=="claim":
        if not args.site: raise ValueError("site is required")
        state=claim_site(state,args.site)
    elif args.action=="assign":
        if args.agent not in AGENTS: raise ValueError("valid agent is required")
        if not args.task: raise ValueError("task is required")
        state=assign(state,args.agent,args.task,args.site or None)
    elif args.action=="verify":
        if not args.agent: raise ValueError("agent is required")
        state=verify(state,args.agent,args.passed.lower()=="true",args.error or None)
    elif args.action=="complete":
        state=complete_site(state)
    elif args.action=="fail":
        state=fail_site(state,args.error or "Runtime failure")
    save(STATE,state)
    status=load(STATUS,{})
    if not isinstance(status,dict): status={}
    status["agent_runtime"]=state
    status["runtime_command"]={"action":args.action,"agent":args.agent or None,"site":args.site or None,"task":args.task or None,"result":"applied"}
    save(STATUS,status)
    print(json.dumps(status["runtime_command"],indent=2))

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print("Runtime command rejected:",exc,file=sys.stderr); raise SystemExit(1)
