const $=id=>document.getElementById(id);
const ACTIONS_URL="https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/workflows/monitor.yml";
async function loadStatus(){
 try{
  const r=await fetch("public/status.json?ts="+Date.now(),{cache:"no-store"});
  if(!r.ok) throw new Error("status unavailable");
  const s=await r.json();
  $("controller").textContent=s.ok?"Online":"Needs attention";
  $("lastRun").textContent=s.finished_at?new Date(s.finished_at).toLocaleString():"Not run";
  $("repos").textContent=String(s.targets_configured??0);
  $("sources").textContent=String(s.sources_checked??0);
  $("discovered").textContent=String((s.discovered||[]).length);
  $("status").textContent=s.ok?"● Online":"● Warning";
  const lines=[];
  if(s.finished_at) lines.push("Last run: "+s.finished_at);
  if((s.discovered||[]).length) lines.push("Discovered: "+s.discovered.length+" item(s)");
  if((s.errors||[]).length) lines.push("Errors: "+s.errors.length);
  $("log").textContent=lines.join("\n")||"Controller has not run yet.";
 }catch(e){ $("controller").textContent="Waiting"; $("status").textContent="● Waiting"; $("log").textContent="Status artifact is not available yet."; }
}
$("refresh").onclick=loadStatus;
$("run").onclick=()=>window.open(ACTIONS_URL,"_blank");
loadStatus(); setInterval(loadStatus,60000);