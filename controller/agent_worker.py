"""Deterministic GitHub Agent Runtime worker."""
from __future__ import annotations
import json, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
STATE=ROOT/"controller"/"agent_state.json"
STATUS=ROOT/"public"/"status.json"
SITES=ROOT/"controller"/"sites.json"
NORMAL=["manager","researcher","image-agent","publisher","seo-agent","qa"]
REPAIR=["bug-hunter","bug-solver","qa"]

def load(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())

def verify_workspace():
    required=[ROOT/"index.html",ROOT/"package.json",ROOT/"src"/"main.tsx",ROOT/"src"/"styles.css"]
    missing=[str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        return False,"Missing required workspace files: "+", ".join(missing)
    try:
        json.loads((ROOT/"package.json").read_text(encoding="utf-8"))
        json.loads(SITES.read_text(encoding="utf-8"))
    except Exception as exc:
        return False,"Invalid JSON configuration: "+str(exc)
    return True,"Workspace structure and configuration verified."

def main():
    if len(sys.argv)!=2: raise SystemExit("usage: agent_worker.py SITE_ID")
    site_id=sys.argv[1]
    registry=load(SITES,{"sites":[]})
    site=next((s for s in registry.get("sites",[]) if s.get("id")==site_id),None)
    if not site or not site.get("enabled") or not site.get("authorized"):
        raise RuntimeError("Site is not enabled and authorized")
    policy=load(ROOT/"agents"/"registry.json",{})
    retry_limit=max(1,int(policy.get("execution",{}).get("max_retries",3)))
    st=load(STATE,{"active_site":None,"agent_states":{},"events":[]})
    active=st.get("active_site")
    if active is None:
        active={"id":site_id,"state":"CLAIMED","retries":0,"flow":NORMAL,"pipeline_index":0}
        st["active_site"]=active
    elif active.get("id")!=site_id:
        raise RuntimeError("Another site is active: "+str(active.get("id")))
    if active.get("state")=="BLOCKED":
        raise RuntimeError(
            "Active site is blocked after "+str(retry_limit)+
            " failed attempts; manual review is required before retrying."
        )

    flow=active.get("flow",NORMAL)
    idx=int(active.get("pipeline_index",0))
    if idx>=len(flow):
        if flow==REPAIR:
            raise RuntimeError("Repair flow exhausted without QA success")
        st["active_site"]=None
        st.setdefault("events",[]).append({"type":"site_completed","site":site_id,"at":now()})
        save(STATE,st)
        save(STATUS,{"ok":True,"agent_runtime":st,"runtime_result":{"site":site_id,"completed":True}})
        return

    agent=flow[idx]
    tasks={
      "manager":"Validate and coordinate the active site",
      "researcher":"Validate authorized research routes",
      "image-agent":"Validate authorized media policy",
      "publisher":"Validate publication workspace",
      "seo-agent":"Validate core SEO and deployable files",
      "qa":"Run final verification",
      "bug-hunter":"Diagnose the failed step",
      "bug-solver":"Apply a safe deterministic repair"
    }

    try:
        if agent=="researcher" and not site.get("routes"):
            raise RuntimeError("No authorized routes configured")
        if agent=="image-agent" and site.get("media",{}).get("enabled") and not site.get("media",{}).get("authorized_source"):
            raise RuntimeError("Authorized media source is missing")
        if agent in ("publisher","qa","bug-solver"):
            passed,detail=verify_workspace()
            if not passed:
                raise RuntimeError(detail)
        if agent=="seo-agent" and not (ROOT/"index.html").exists():
            raise RuntimeError("index.html is missing")
        if agent=="bug-hunter":
            active["diagnosis"]="Failure isolated for repair; QA must pass before completion."

        states=st.setdefault("agent_states",{})
        states.setdefault(agent,{})
        states[agent].update({
            "state":"VERIFYING" if agent=="qa" else "WORKING",
            "site":site_id,"task":tasks[agent],"error":None
        })
        st.setdefault("events",[]).append({
            "type":"agent_step","agent":agent,"site":site_id,
            "task":tasks[agent],"at":now()
        })

        if agent=="qa":
            # QA is the final gate. Reset all agents involved in this
            # completed flow so the persistent state matches the UI.
            for completed_agent in flow:
                agent_state = states.setdefault(completed_agent,{})
                agent_state.update({
                    "state":"IDLE",
                    "site":None,
                    "task":None,
                    "error":None
                })
            states[agent]["state"]="COMPLETED"
            st["active_site"]=None
            st["events"].append({
                "type":"site_repaired_and_completed" if flow==REPAIR else "site_completed",
                "site":site_id,"at":now()
            })
        else:
            active["pipeline_index"]=idx+1
            active["state"]="WORKING"

        save(STATE,st)
        save(STATUS,{"ok":True,"agent_runtime":st,
                     "runtime_result":{"agent":agent,"site":site_id,
                                       "task":tasks[agent],"passed":True}})
    except Exception as exc:
        states=st.setdefault("agent_states",{})
        states.setdefault(agent,{})
        states[agent].update({
            "state":"FAILED","site":site_id,
            "task":tasks[agent],"error":str(exc)
        })
        active["failed_agent"]=agent
        active["error"]=str(exc)
        active["retries"]=int(active.get("retries",0))+1
        blocked=active["retries"]>=retry_limit
        if blocked:
            # Keep the active-site lock so later sites cannot skip a failed site.
            # A blocked site requires an explicit human review/reset.
            active["state"]="BLOCKED"
            states[agent]["state"]="FAILED"
            event_type="repair_exhausted"
        else:
            active["state"]="REPAIRING"
            active["flow"]=REPAIR
            active["pipeline_index"]=0
            event_type="agent_step_failed"
        st.setdefault("events",[]).append({
            "type":event_type,"agent":agent,
            "site":site_id,"error":str(exc),
            "retries":active["retries"],"retry_limit":retry_limit,"at":now()
        })
        save(STATE,st)
        save(STATUS,{"ok":False,"agent_runtime":st,
                     "runtime_result":{"agent":agent,"site":site_id,
                                       "passed":False,"blocked":blocked,
                                       "retries":active["retries"],
                                       "retry_limit":retry_limit,
                                       "error":str(exc),
                                       "repair_flow":None if blocked else REPAIR}})
        raise

if __name__=="__main__":
    main()
