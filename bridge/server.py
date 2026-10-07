#!/usr/bin/env python3
"""Free local bridge: browser -> protected GitHub Actions Agent Runtime."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json, os, urllib.request, urllib.error

HOST="127.0.0.1"; PORT=8787
OWNER="WebControlerAgent"; REPO="WebControlerAgent.github.io"
WORKFLOW="agent-dispatch.yml"
TOKEN=os.environ.get("GITHUB_TOKEN","")

class Handler(BaseHTTPRequestHandler):
    def send_json(self, code, data):
        raw=json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","https://webcontroleragent.github.io")
        self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers(); self.wfile.write(raw)
    def do_OPTIONS(self): self.send_json(204,{})
    def do_GET(self):
        if self.path!="/health": return self.send_json(404,{"ok":False,"error":"Not found"})
        self.send_json(200,{"ok":True,"bridge":"Agent Runtime Bridge","token_configured":bool(TOKEN)})
    def do_POST(self):
        if self.path!="/dispatch": return self.send_json(404,{"ok":False,"error":"Not found"})
        if not TOKEN: return self.send_json(503,{"ok":False,"error":"GITHUB_TOKEN is not configured"})
        try:
            n=int(self.headers.get("Content-Length","0")); p=json.loads(self.rfile.read(n) or b"{}")
            action=p.get("action")
            if action not in {"claim","assign","verify","complete","fail"}: return self.send_json(400,{"ok":False,"error":"Invalid runtime action"})
            allowed={"site","agent","task","passed","error"}
            inputs={k:str(v) for k,v in p.items() if k in allowed and v is not None}
            body=json.dumps({"ref":"main","inputs":{"action":action,**inputs}}).encode()
            url=f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/{WORKFLOW}/dispatches"
            req=urllib.request.Request(url,data=body,method="POST",headers={"Accept":"application/vnd.github+json","Authorization":f"Bearer {TOKEN}","X-GitHub-Api-Version":"2022-11-28","Content-Type":"application/json","User-Agent":"Agent-Runtime-Bridge"})
            with urllib.request.urlopen(req,timeout=20) as res:
                if res.status not in (200,201,202,204): raise RuntimeError(f"GitHub returned HTTP {res.status}")
            self.send_json(200,{"ok":True,"dispatched":True,"action":action})
        except urllib.error.HTTPError as e:
            self.send_json(502,{"ok":False,"error":f"GitHub HTTP {e.code}: {e.read().decode(errors='replace')[:500]}"})
        except Exception as e: self.send_json(500,{"ok":False,"error":str(e)})
    def log_message(self,*args): pass

if __name__=="__main__":
    print(f"Agent Runtime Bridge: http://{HOST}:{PORT}")
    if not TOKEN: print("Set GITHUB_TOKEN before starting.")
    HTTPServer((HOST,PORT),Handler).serve_forever()
