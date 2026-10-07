export type RuntimeAction = {
  action:"claim"|"assign"|"verify"|"complete"|"fail";
  site?:string; agent?:string; task?:string; passed?:boolean; error?:string;
};
export type ChatReply = { text:string; agentId:string; runtimeAction?:RuntimeAction; aiRequest?:string };

type AgentSnapshot = { id:string; name:string; role:string; status:string; task:string };

export function managerReply(input:string, agents:AgentSnapshot[], runtime:any):ChatReply {
  const q=input.trim().toLowerCase();
  const runtimeAgents=runtime?.agent_runtime?.agent_states ?? {};
  if(!q) return {agentId:"manager",text:"Haan jani, command ya task batao. Main Manager Runtime ko route karunga."};

  if(q.includes("status")||q.includes("report")){
    const active=runtime?.agent_runtime?.active_site?.id ?? "koi active site nahi";
    const states=Object.values(runtimeAgents) as any[];
    const working=states.filter(a=>a.state==="WORKING").map(a=>a.name);
    return {agentId:"manager",text:"Actual Runtime: active site = "+active+". Working agents: "+(working.length?working.join(", "):"none")+". One-site-at-a-time lock active hai."};
  }

  const focus=agents.find(a=>q.includes(a.name.toLowerCase())||q.includes(a.id));
  if(focus){
    const rs=runtimeAgents[focus.id];
    return {agentId:focus.id,text:focus.name+" — Runtime state: "+(rs?.state??focus.status)+". Task: "+(rs?.task??focus.task??"none")+"."};
  }

  const claim=q.match(/(?:claim|start|open)\s+(?:site\s+)?([a-z0-9._/-]+)/i);
  if(claim){
    return {agentId:"manager",text:"Runtime command prepared: claim site "+claim[1]+". Execute it through the protected GitHub Actions runtime.",runtimeAction:{action:"claim",site:claim[1]}};
  }

  const assign=q.match(/(?:assign|give)\s+([a-z0-9-]+)\s+(.+)/i);
  if(assign && agents.some(a=>a.id===assign[1])){
    return {agentId:assign[1],text:"Runtime command prepared for "+assign[1]+".",runtimeAction:{action:"assign",agent:assign[1],task:assign[2]}};
  }

  if(q.includes("complete")){
    return {agentId:"manager",text:"Runtime completion command prepared. It will release the active-site lock after execution.",runtimeAction:{action:"complete"}};
  }

  if(q.includes("bug")||q.includes("error")||q.includes("fail")){
    return {agentId:"bug-hunter",text:"Failure flow is Bug Hunter → Bug Solver → QA. I prepared the runtime repair path; the active site remains blocked until verification passes.",runtimeAction:{action:"fail",agent:"bug-hunter",error:input}};
  }

  if(q.includes("next")||q.includes("queue")){
    const site=runtime?.agent_runtime?.active_site?.id;
    return {agentId:"manager",text:site?"Current site "+site+" must complete/verify before the next site starts.":"Queue is ready; Manager will claim the next authorized site when available."};
  }

  return {agentId:"manager",text:"Instruction received. For real Manager reasoning, send this instruction to the protected Manager AI workflow; the public page never receives the AI secret.",aiRequest:input};
}
