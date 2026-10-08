"""Manage authorized Agent Studio sites from a protected GitHub Issue."""
from __future__ import annotations
import json, os, re
from urllib.parse import urlparse
OWNER="WebControlerAgent"
ALLOWED={"add","update","enable","disable","remove"}
def valid_id(v): return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", v or ""))
def valid_url(v):
    p=urlparse(v or ""); return p.scheme in {"http","https"} and bool(p.netloc)
def main():
    event=json.load(open(os.environ["GITHUB_EVENT_PATH"],encoding="utf-8"))
    issue=event.get("issue",{}); author=(issue.get("user") or {}).get("login","")
    association=issue.get("author_association","")
    if author.lower()!=OWNER.lower() and association!="OWNER": raise PermissionError("Issue author is not authorized")
    if not (issue.get("title") or "").startswith("[Site Manager]"): raise ValueError("Not a Site Manager issue")
    body=issue.get("body") or ""
    m=re.search(r"<!--\s*site-manager-command\s*(\{.*?\})\s*-->",body,re.S)
    if not m: raise ValueError("Missing site-manager-command block")
    cmd=json.loads(m.group(1)); action=cmd.get("action")
    if action not in ALLOWED: raise ValueError("Invalid site action")
    sites_doc=json.load(open("controller/sites.json",encoding="utf-8")); sites=sites_doc.setdefault("sites",[])
    sid=str(cmd.get("id","")).strip().lower()
    if not valid_id(sid): raise ValueError("Invalid site id")
    found=next((s for s in sites if s.get("id")==sid),None)
    if action=="add":
        if found: raise ValueError("Site id already exists")
        if any(not str(cmd.get(k,"")).strip() for k in ("name","repository","branch","live_url")): raise ValueError("Missing required site field")
        if not valid_url(cmd["live_url"]): raise ValueError("Invalid live_url")
        if cmd.get("authorized") is not True: raise PermissionError("Only explicitly authorized sites may be added")
        media=bool(cmd.get("media_enabled",False))
        sites.append({"id":sid,"name":str(cmd["name"]).strip(),"repository":str(cmd["repository"]).strip(),"branch":str(cmd["branch"]).strip(),"live_url":str(cmd["live_url"]).strip(),"enabled":bool(cmd.get("enabled",True)),"authorized":True,"routes":["authorized-github-repository"],"media":{"enabled":media,"authorized_source":media,"path":str(cmd.get("media_path","")).strip()},"description":str(cmd.get("description","")).strip(),"runtime_test":"site-manager-added"})
    elif action=="remove":
        if not found: raise ValueError("Site not found")
        sites.remove(found)
    else:
        if not found: raise ValueError("Site not found")
        if action=="enable": found["enabled"]=True
        elif action=="disable": found["enabled"]=False
        elif action=="update":
            for k in ("name","repository","branch","description"):
                if k in cmd: found[k]=str(cmd[k]).strip()
            if "live_url" in cmd:
                if not valid_url(cmd["live_url"]): raise ValueError("Invalid live_url")
                found["live_url"]=str(cmd["live_url"]).strip()
            if "media_enabled" in cmd: found.setdefault("media",{})["enabled"]=bool(cmd["media_enabled"])
            if "media_path" in cmd: found.setdefault("media",{})["path"]=str(cmd["media_path"]).strip()
    sites_doc["version"]=1; sites_doc["policy"]={"one_active_site":True,"authorized_only":True}
    payload=json.dumps(sites_doc,ensure_ascii=False,indent=2)+"\n"
    open("controller/sites.json","w",encoding="utf-8").write(payload)
    open("public/sites.json","w",encoding="utf-8").write(payload)
    print("Site manager action applied:",action,sid)
if __name__=="__main__": main()
