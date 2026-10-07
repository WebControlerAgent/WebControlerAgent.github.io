"""Deterministic GitHub Agent Runtime worker."""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
STATE=ROOT/"controller"/"agent_state.json"
STATUS=ROOT/"public"/"status.json"
SITES=ROOT/"sites"/"registry.json"
PIPELINE=["manager","researcher","image-agent","publisher","seo-agent","qa"]

def load(path, default):
    if not path.exists(): return default
    return json.loads(path.read_text(encoding="utf-8"))

def save(path, value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

def main():
    if len(sys.argv)!=2: raise SystemExit("usage: agent_worker.py SITE_ID")
    site_id=sys.argv[1]
    registry=load(SITES,{"sites":[]})
    site=next((s for s in registry.get("sites",[]) if s.get("id")==site_id),None)
    if not site or not site.get("enabled") or not site.get("authorized"):
        raise RuntimeError("Site is not enabled and authorized")
    st=load(STATE,{})
    active=st.get("active_site")
    if active is None:
        active={"id":site_id,"state":"CLAIMED","retries":0,"pipeline_index":0}
        st["active_site"]=active
    elif active.get("id")!=site_id:
        raise RuntimeError("Another site is active")
    idx=int(active.get("pipeline_index",0))
    if idx>=len(PIPELINE):
        st["active_site"]=None
        save(STATE,st)
        return
    agent=PIPELINE[idx]
    tasks={
      "manager":"Validate and coordinate the active site",
      "researcher":"Validate authorized research routes",
      "image-agent":"Validate authorized media policy",
      "publisher":"Prepare the site for deployment",
      "seo-agent":"Validate core SEO/deployable files",
      "qa":"Run final verification"
    }
    task=tasks[agent]
    if agent=="researcher" and not site.get("routes"):
        raise RuntimeError("No authorized routes configured")
    if agent=="image-agent" and site.get("media",{}).get("enabled") and not site.get("media",{}).get("authorized_source"):
        raise RuntimeError("Authorized media source is missing")
    if agent=="seo-agent" and not (ROOT/"index.html").exists():
        raise RuntimeError("index.html is missing")
    states=st.setdefault("agent_states",{})
    states.setdefault(agent,{})
    states[agent].update({"state":"WORKING","site":site_id,"task":task,"error":None})
    active["pipeline_index"]=idx+1
    st.setdefault("events",[]).append({"type":"agent_step","agent":agent,"site":site_id,"task":task,"at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())})
    if agent=="qa":
        states[agent]["state"]="VERIFYING"
        st["active_site"]=None
        st["events"].append({"type":"site_completed","site":site_id})
    save(STATE,st)
    save(STATUS,{"ok":True,"agent_runtime":st,"runtime_result":{"agent":agent,"site":site_id,"task":task,"next_index":active["pipeline_index"]}})
    print(json.dumps({"agent":agent,"site":site_id,"task":task}))
if __name__=="__main__":
    main()
