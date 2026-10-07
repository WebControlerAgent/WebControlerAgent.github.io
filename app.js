const $=id=>document.getElementById(id);
const ACTIONS_URL="https://github.com/WebControlerAgent/WebControlerAgent.github.io/actions/workflows/monitor.yml";
const agentData={
 manager:["Manager","Team Lead","🧑‍💼","Managing queue and coordinating the team."],
 researcher:["Researcher","Research & Discovery","🧑‍🔬","Waiting for an authorized research task."],
 "image-agent":["Image Agent","Authorized Media Worker","🧑‍🎨","Waiting for an authorized media task."],
 "bug-hunter":["Bug Hunter","Find & Diagnose","🕵️","Monitoring for failures."],
 "seo-agent":["SEO Agent","Search Specialist","👩‍💻","Waiting for an SEO task."],
 "idea-builder":["Idea Builder","New Site Ideas","💡","Thinking about future site ideas."],
 publisher:["Publisher","Build & Deploy","📤","Waiting for a verified build."],
 qa:["QA Agent","Final Verification","🧪","Waiting for the final verification stage."],
 "bug-solver":["Bug Solver","Repair & Fix","🧑‍🔧","Waiting for an authorized repair task."]
};
function addChat(who,msg){const box=document.createElement("div");box.className="bubble";box.innerHTML="<b>"+who+"</b><p>"+msg.replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]))+"</p>";$("chatLog").appendChild(box);$("chatLog").scrollTop=$("chatLog").scrollHeight}
function openAgent(id){const a=agentData[id]||agentData.manager;const source=document.querySelector(`.desk[data-agent="${id}"] .person`);const avatar=$("modalAvatar");avatar.innerHTML="";if(source){const clone=source.cloneNode(true);clone.classList.remove("typing");clone.classList.add("modal-person");avatar.appendChild(clone)}else{avatar.textContent=a[2]}$("modalName").textContent=a[0];$("modalRole").textContent=a[1];$("modalState").textContent="READY";$("modalTask").textContent=a[3];$("agentModal").classList.remove("hidden")}
document.querySelectorAll(".desk").forEach(d=>d.addEventListener("click",()=>openAgent(d.dataset.agent)));
$("closeModal").onclick=()=>$("agentModal").classList.add("hidden");
$("agentModal").addEventListener("click",e=>{if(e.target.id==="agentModal")$("agentModal").classList.add("hidden")});
$("modalChat").onclick=()=>{$("agentModal").classList.add("hidden");$("chatInput").focus();addChat("Manager","Employee channel opened. Tell me what you want the team to do.");};
async function loadStatus(){
 try{
  const r=await fetch("public/status.json?ts="+Date.now(),{cache:"no-store"});if(!r.ok)throw new Error();
  const s=await r.json();const sites=Array.isArray(s.targets)?s.targets:[];
  $("controller").textContent=s.ok?"Online":"Needs attention";$("lastRun").textContent=s.finished_at?new Date(s.finished_at).toLocaleString():"Not run";
  $("repos").textContent=String(s.targets_configured??sites.length??0);$("sources").textContent=String(s.sources_checked??0);$("discovered").textContent=String((s.discovered||[]).length);
  $("status").textContent=s.ok?"● SYSTEM READY":"● ATTENTION";$("managerStatus").textContent=s.ok?"READY":"CHECK";
  $("queueCount").textContent=sites.length+" sites";$("nextSite").textContent=sites[0]?.name||"Waiting for queue";
  $("queue").innerHTML=sites.length?sites.slice(0,8).map((x,i)=>'<div class="queue-item"><span>'+(i===0?"🟢 ":"⚪ ")+(x.name||x.repo||"Site")+'</span><small>'+((x.status||"WAITING").toUpperCase())+'</small></div>').join(""):'<div class="empty">No sites configured yet.</div>';
 }catch(e){$("controller").textContent="Waiting";$("managerStatus").textContent="WAIT";$("status").textContent="● WAITING"}
}
$("refresh").onclick=loadStatus;$("run").onclick=()=>window.open(ACTIONS_URL,"_blank");
$("chatForm").addEventListener("submit",e=>{e.preventDefault();const v=$("chatInput").value.trim();if(!v)return;addChat("You",v);$("chatInput").value="";const q=v.toLowerCase();let reply="I’m the Studio Manager. I can read dashboard status, explain the team, and coordinate authorized tasks one site at a time.";if(q.includes("status")||q.includes("haal"))reply="Current dashboard: "+$("controller").textContent+". Sites: "+$("repos").textContent+". Last run: "+$("lastRun").textContent+".";else if(q.includes("site"))reply="Single-site mode is active: one site must finish and verify before the next site starts.";else if(q.includes("agent")||q.includes("employee"))reply="Click any employee in the office to open their character panel. The team includes Manager, Researcher, Image Agent, SEO Agent, Bug Hunter, Idea Builder, Publisher and QA Agent.";else if(q.includes("run")||q.includes("start"))reply="The workflow monitor is ready. Use the Run Monitor button for the authorized GitHub Actions run.";setTimeout(()=>addChat("Manager",reply),250)});
loadStatus();setInterval(loadStatus,60000);