export type ChatReply = { text: string; agentId: string };

type AgentSnapshot = { id: string; name: string; role: string; status: string; task: string };

export function managerReply(input: string, agents: AgentSnapshot[], runtime: any): ChatReply {
  const q = input.trim().toLowerCase();
  if (!q) return {agentId:"manager", text:"Haan jani, command ya task batao. Main agents ko route karunga."};

  if (q.includes("status") || q.includes("report")) {
    const active = runtime?.agent_runtime?.active_site?.id ?? "koi active site nahi";
    const working = agents.filter(a => a.status === "WORKING").map(a => a.name);
    return {agentId:"manager", text:"Runtime status: active site = " + active + ". Working agents: " + (working.length ? working.join(", ") : "none") + ". One-site-at-a-time lock active hai."};
  }

  const focus = agents.find(a => q.includes(a.name.toLowerCase()) || q.includes(a.id));
  if (focus) return {agentId:focus.id, text:focus.name + " ka current state " + focus.status + " hai. Current task: " + focus.task + "."};

  if (q.includes("next") || q.includes("queue")) {
    const site = runtime?.agent_runtime?.active_site?.id;
    return {agentId:"manager", text:site ? "Current site " + site + " complete/verify hone tak next site start nahi hogi." : "Queue ready hai; Manager next authorized site ko claim karega jab runtime mein site available hogi."};
  }

  if (q.includes("bug") || q.includes("error") || q.includes("fail")) {
    return {agentId:"bug-hunter", text:"Failure detect hone par flow Bug Hunter → Bug Solver → QA hai. Main next site ko block rakhunga jab tak verification pass nahi hoti."};
  }

  return {agentId:"manager", text:"Samajh gaya. Command Manager channel mein receive ho gayi. Real execution sirf configured agent tools aur authorized routes ke through hogi."};
}
