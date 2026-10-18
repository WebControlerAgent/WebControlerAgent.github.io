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
function openAgent(id){const a=agentData[id]||agentData.manager;const source=document.querySelector(`.desk[data-agent="${id}"] .character`);const avatar=$("modalAvatar");avatar.innerHTML="";if(source){const clone=source.cloneNode(true);clone.classList.remove("typing");clone.classList.add("modal-person");avatar.appendChild(clone)}else{avatar.textContent=a[2]}$("modalName").textContent=a[0];$("modalRole").textContent=a[1];$("modalState").textContent="READY";$("modalTask").textContent=a[3];$("agentModal").classList.remove("hidden")}
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
function getBridgeConfig(){
 let url=sessionStorage.getItem("aiwcu_bridge_url")||"";
 let key=sessionStorage.getItem("aiwcu_chat_key")||"";
 if(!url){url=prompt("Paste your deployed AIWCU Cloudflare Worker URL (https://...workers.dev):")||"";url=url.trim().replace(/\/+$/,"");}
 if(!/^https:\/\//i.test(url)){addChat("Manager","Secure bridge URL required. Deploy the Worker using worker/README.md, then enter its HTTPS URL.");return null;}
 if(!key){key=prompt("Enter your private AIWCU chat key (AIWCU_CHAT_KEY):")||"";key=key.trim();}
 if(!key){addChat("Manager","No private chat key entered. Command was not sent.");return null;}
 sessionStorage.setItem("aiwcu_bridge_url",url);sessionStorage.setItem("aiwcu_chat_key",key);
 return {url,key};
}
async function sendManagerInstruction(instruction){
 const cfg=getBridgeConfig();if(!cfg)return;
 addChat("Manager","Submitting your instruction to the protected GitHub workflow…");
 try{
  const response=await fetch(cfg.url+"/command",{method:"POST",headers:{"Content-Type":"application/json","Authorization":"Bearer "+cfg.key},body:JSON.stringify({instruction})});
  const data=await response.json().catch(()=>({}));
  if(!response.ok)throw new Error(data.error||("Bridge request failed ("+response.status+")."));
  if(!data.issue)throw new Error("Bridge response did not include a GitHub issue number.");
  addChat("Manager","Command submitted to GitHub Actions (issue #"+data.issue+"). I’m checking for the workflow response now.");
  const seenComments=new Set();
  for(let attempt=0;attempt<20;attempt++){
   if(attempt>0)await new Promise(resolve=>setTimeout(resolve,4000));
   const resultResponse=await fetch(cfg.url+"/result?issue="+encodeURIComponent(data.issue),{headers:{"Authorization":"Bearer "+cfg.key},cache:"no-store"});
   const result=await resultResponse.json().catch(()=>({}));
   if(!resultResponse.ok)throw new Error(result.error||("Result check failed ("+resultResponse.status+")."));
   const comments=Array.isArray(result.comments)?result.comments:[];
   for(const comment of comments){
    const body=String(comment.body||"").trim();
    const signature=String(comment.author||"")+":"+body;
    if(!body||seenComments.has(signature)||body.includes("[RUNTIME_PENDING]"))continue;
    seenComments.add(signature);
    if(body.startsWith("🤖 **Manager AI:**")){addChat("Manager",body.replace(/^🤖 \*\*Manager AI:\*\*\s*/,""));}
    else if(body.includes("Agent Runtime")||body.includes("Agent pipeline")||body.includes("Runtime state transition")||body.includes("Assignment recorded")){addChat("Manager",body);}
   }
   const latest=comments.map(c=>String(c.body||"")).join("\n");
   if(latest.includes("Agent pipeline completed successfully")||latest.includes("Agent Runtime command failed")||latest.includes("Runtime state transition applied")||latest.includes("Assignment recorded; execution not started"))return;
  }
  addChat("Manager","GitHub accepted the command, but the final result has not arrived in the chat's 80-second check window. Open the linked issue to follow its Actions run: "+data.issueUrl);
 }catch(error){addChat("Manager","Command was not confirmed: "+String(error.message||error)+" Check the Worker URL, ALLOWED_ORIGIN, private key, and GitHub token setup.");}
}
$("chatForm").addEventListener("submit",async e=>{
 e.preventDefault();const v=$("chatInput").value.trim();if(!v)return;addChat("You",v);$("chatInput").value="";const q=v.toLowerCase();
 if(q==="help"||q.includes("what can you do")||q.includes("team members")){addChat("Manager","I can submit authorized instructions to the protected GitHub Manager workflow. Runtime actions are limited by the repository workflows and verification gates. Ask for dashboard status locally, or give a task to send it to GitHub.");return;}
 if(q.includes("status")||q.includes("haal")){addChat("Manager","Current dashboard: "+$("controller").textContent+". Sites: "+$("repos").textContent+". Last run: "+$("lastRun").textContent+".");return;}
 if(q.includes("agent")||q.includes("employee")){addChat("Manager","Team shown in the office: Manager, Researcher, Image Agent, SEO Agent, Bug Hunter, Idea Builder, Publisher and QA Agent. Send a specific task if you want it submitted to GitHub.");return;}
 await sendManagerInstruction(v);
});
loadStatus();setInterval(loadStatus,60000);
