import json
import os
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "controller" / "config.json"
STATE = ROOT / "controller" / "state.json"
STATUS = ROOT / "public" / "status.json"
AGENT_STATE = ROOT / "controller" / "agent_state.json"

def load(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def path_get(obj, dotted):
    cur = obj
    for part in dotted.split(".") if dotted else []:
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur

def fetch_json(source):
    headers = {"User-Agent": "WebControllerAgent/1.0"}
    secret_name = source.get("auth_secret", "").strip()
    if secret_name:
        token = os.environ.get(secret_name, "")
        if token:
            headers["Authorization"] = "Bearer " + token
    req = Request(source["url"], headers=headers)
    with urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))

def main():
    from agent_runtime import normalize
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    cfg = load(CONFIG, {})
    state = load(STATE, {"seen": {}})
    agent_state = normalize(load(AGENT_STATE, None))
    errors, discovered = [], []
    sources = {s["id"]: s for s in cfg.get("sources", []) if s.get("enabled")}
    targets = {t["id"]: t for t in cfg.get("targets", []) if t.get("enabled")}
    routes = cfg.get("routes", [])

    if not cfg.get("policy", {}).get("authorized_sources_only", True):
        raise RuntimeError("Safety policy requires authorized_sources_only=true")

    for route in routes:
        sid, tid = route.get("source_id"), route.get("target_id")
        source, target = sources.get(sid), targets.get(tid)
        if not source or not target:
            continue
        try:
            payload = fetch_json(source)
            items = path_get(payload, source.get("items_path", "items")) or []
            for item in items[:int(cfg.get("limits", {}).get("max_items_per_run", 20))]:
                item_id = str(path_get(item, source.get("id_field", "id")))
                if not item_id or item_id == "None" or state["seen"].get(sid) == item_id:
                    continue
                discovered.append({
                    "source": sid,
                    "target": tid,
                    "id": item_id,
                    "title": path_get(item, source.get("title_field", "title")),
                    "updated": path_get(item, source.get("updated_field", "updated")),
                    "content_url": path_get(item, source.get("content_url_field", "content_url"))
                })
            if items:
                newest = str(path_get(items[0], source.get("id_field", "id")))
                if newest != "None":
                    state["seen"][sid] = newest
        except (HTTPError, URLError, ValueError, KeyError) as exc:
            errors.append({"source": sid, "error": str(exc)})

    status = {
        "ok": not errors,
        "started_at": started,
        "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sources_checked": len(sources),
        "targets_configured": len(targets),
        "discovered": discovered,
        "errors": errors,
        "note": "Discovery only. Publishing requires an explicit authorized target adapter.",
        "agent_runtime": agent_state,
    }
    save(STATE, state)
    save(AGENT_STATE, agent_state)
    save(STATUS, status)
    print(json.dumps(status, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    sys.exit(main())
