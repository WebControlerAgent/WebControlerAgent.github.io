import React,{useEffect,useMemo,useRef,useState} from "react";
import {createRoot} from "react-dom/client";
import {Canvas,useFrame,useThree} from "@react-three/fiber";
import {Html,OrbitControls,Text,useCursor} from "@react-three/drei";
import * as THREE from "three";
import "./styles.css";
import {managerReply} from "./chat/managerChat";

type Status="IDLE"|"WALKING"|"WORKING"|"THINKING"|"MEETING"|"SUCCESS"|"ERROR";
type Agent={id:string;name:string;role:string;color:string;accent:string;desk:[number,number,number];waypoints:[number,number,number][];task:string;status:Status;icon:string};
const agents:Agent[]=[
{id:"bug-solver",name:"Bug Solver",role:"Repair & Fix",color:"#69435d",accent:"#ff9fbd",desk:[7,0,1.2],waypoints:[[7,0,1.2],[5,0,3],[2,0,4],[7,0,1.2]],task:"Repairing verified defects before retry",status:"WORKING",icon:"F"},

{id:"manager",name:"Manager",role:"Team Lead",color:"#355c7d",accent:"#7dd3fc",desk:[-7,0,-4],waypoints:[[-7,0,-4],[-2,0,-1],[0,0,2],[-7,0,-4]],task:"Coordinating the active site queue",status:"WORKING",icon:"M"},
{id:"researcher",name:"Researcher",role:"Research & Discovery",color:"#426b57",accent:"#8be3ad",desk:[-3.5,0,-4],waypoints:[[-3.5,0,-4],[-5,0,1],[-1,0,3],[-3.5,0,-4]],task:"Checking authorized sources",status:"THINKING",icon:"R"},
{id:"image-agent",name:"Image Agent",role:"Authorized Media",color:"#6b4c7c",accent:"#d8a7ff",desk:[0,0,-4],waypoints:[[0,0,-4],[4,0,-1],[5,0,2],[0,0,-4]],task:"Preparing approved media assets",status:"WORKING",icon:"I"},
{id:"bug-hunter",name:"Bug Hunter",role:"Find & Diagnose",color:"#7a5838",accent:"#ffcb7a",desk:[3.5,0,-4],waypoints:[[3.5,0,-4],[5,0,2],[2,0,4],[3.5,0,-4]],task:"Scanning the current build",status:"WALKING",icon:"B"},
{id:"seo-agent",name:"SEO Agent",role:"Search Specialist",color:"#2d6570",accent:"#75e1ed",desk:[7,0,-4],waypoints:[[7,0,-4],[4,0,3],[0,0,3],[7,0,-4]],task:"Optimizing discoverability signals",status:"WORKING",icon:"S"},
{id:"idea-builder",name:"Idea Builder",role:"New Site Ideas",color:"#806b32",accent:"#ffe18a",desk:[-4.8,0,4],waypoints:[[-4.8,0,4],[-1,0,5],[1,0,2],[-4.8,0,4]],task:"Developing the next site concept",status:"THINKING",icon:"N"},
{id:"publisher",name:"Publisher",role:"Build & Deploy",color:"#315d77",accent:"#8fd4ff",desk:[0,0,4],waypoints:[[0,0,4],[5,0,4],[6,0,1],[0,0,4]],task:"Preparing a verified deployment",status:"WORKING",icon:"P"},
{id:"qa",name:"QA Agent",role:"Final Verification",color:"#35665c",accent:"#8df0c2",desk:[4.8,0,4],waypoints:[[4.8,0,4],[2,0,1],[-2,0,1],[4.8,0,4]],task:"Running final verification checks",status:"SUCCESS",icon:"Q"}
];

const statusTone=(s:Status)=>({IDLE:"#718096",WALKING:"#60a5fa",WORKING:"#4ade80",THINKING:"#c084fc",MEETING:"#fbbf24",SUCCESS:"#34d399",ERROR:"#fb7185"}[s]);

function Label({children,color="#dce8f2"}:{children:React.ReactNode;color?:string}){return <Html center distanceFactor={10} position={[0,1.9,0]}><div className="world-label" style={{borderColor:color+"55"}}>{children}</div></Html>}

function Character({agent,selected,onSelect}:{agent:Agent;selected:boolean;onSelect:()=>void}){
 const ref=useRef<THREE.Group>(null); const [i,setI]=useState(0); const [pos]=useState(()=>new THREE.Vector3(...agent.waypoints[0])); const rot=useRef(0); const [hover,setHover]=useState(false);
 useCursor(hover);
 useEffect(()=>{const t=setInterval(()=>setI(v=>(v+1)%agent.waypoints.length),4200);return()=>clearInterval(t)},[agent.waypoints.length]);
 useFrame((_,dt)=>{
   if(!ref.current)return;
   const target=new THREE.Vector3(...agent.waypoints[i]); const d=target.clone().sub(pos); const moving=d.length()>0.06;
   if(moving){const step=Math.min(d.length(),dt*1.7);d.normalize();pos.addScaledVector(d,step);rot.current=Math.atan2(d.x,d.z);}
   ref.current.position.copy(pos); ref.current.rotation.y=THREE.MathUtils.lerp(ref.current.rotation.y,rot.current,.12);
   const bob=agent.status==="WORKING"||moving?Math.sin(performance.now()/170)*.035:Math.sin(performance.now()/850)*.012;
   ref.current.position.y=bob;
 });
 return <group ref={ref} onClick={(e)=>{e.stopPropagation();onSelect()}} onPointerOver={()=>setHover(true)} onPointerOut={()=>setHover(false)}>
   {selected&&<mesh position={[0,.04,0]} rotation={[-Math.PI/2,0,0]}><ringGeometry args={[.58,.72,32]}/><meshBasicMaterial color={agent.accent} transparent opacity={.55}/></mesh>}
   <mesh position={[0,1.18,0]}><boxGeometry args={[.55,.55,.55]}/><meshStandardMaterial color="#e9b28a"/></mesh>
   <mesh position={[0,1.5,0]}><boxGeometry args={[.64,.22,.62]}/><meshStandardMaterial color="#202936"/></mesh>
   <mesh position={[0,.72,0]}><boxGeometry args={[.72,.72,.45]}/><meshStandardMaterial color={agent.color}/></mesh>
   <mesh position={[-.19,.18,0]}><boxGeometry args={[.19,.55,.22]}/><meshStandardMaterial color="#202b38"/></mesh>
   <mesh position={[.19,.18,0]}><boxGeometry args={[.19,.55,.22]}/><meshStandardMaterial color="#202b38"/></mesh>
   <mesh position={[-.48,.78,0]} rotation={[0,0,.28]}><capsuleGeometry args={[.09,.42,4,8]}/><meshStandardMaterial color="#e9b28a"/></mesh>
   <mesh position={[.48,.78,0]} rotation={[0,0,-.28]}><capsuleGeometry args={[.09,.42,4,8]}/><meshStandardMaterial color="#e9b28a"/></mesh>
   <Label color={selected?agent.accent:"#6f8497"}><b>{agent.name}</b><span style={{color:statusTone(agent.status)}}>● {agent.status}</span></Label>
   {hover&&<Html center position={[0,2.5,0]}><div className="task-bubble-3d"><b>{agent.task}</b><small>Click to inspect</small></div></Html>}
 </group>
}

function Desk({position,name,accent}:{position:[number,number,number];name:string;accent:string}){
 return <group position={position}>
   <mesh position={[0,.65,0]}><boxGeometry args={[2.2,.12,1.15]}/><meshStandardMaterial color="#4a5968"/></mesh>
   <mesh position={[-.9,.32,-.38]}><boxGeometry args={[.1,.6,.1]}/><meshStandardMaterial color="#283442"/></mesh>
   <mesh position={[.9,.32,-.38]}><boxGeometry args={[.1,.6,.1]}/><meshStandardMaterial color="#283442"/></mesh>
   <mesh position={[0,1.08,-.25]}><boxGeometry args={[.95,.58,.1]}/><meshStandardMaterial color="#111a24" emissive={accent} emissiveIntensity={.12}/></mesh>
   <mesh position={[0,.77,.18]}><boxGeometry args={[.65,.06,.28]}/><meshStandardMaterial color="#202b36"/></mesh>
   <mesh position={[0,.92,.43]}><boxGeometry args={[.5,.03,.18]}/><meshStandardMaterial color="#10171e"/></mesh>
   <mesh position={[0,.32,.48]}><boxGeometry args={[.75,.06,.65]}/><meshStandardMaterial color="#34414e"/></mesh>
   <Text position={[0,.05,.64]} rotation={[-Math.PI/2,0,0]} fontSize={.12} color="#71879a" anchorX="center">{name}</Text>
 </group>
}

function Zone({position,size,label,accent}:{position:[number,number,number];size:[number,number];label:string;accent:string}){
 return <group position={position}><mesh rotation={[-Math.PI/2,0,0]}><planeGeometry args={size}/><meshStandardMaterial color="#101a25" transparent opacity={.72}/></mesh><Text position={[0,.03,-size[1]/2+.25]} rotation={[-Math.PI/2,0,0]} fontSize={.16} color={accent} anchorX="center">{label}</Text></group>
}

function Office({selected,setSelected}:{selected:string|null;setSelected:(id:string)=>void}){
 return <group>
  <mesh rotation={[-Math.PI/2,0,0]}><planeGeometry args={[22,14]}/><meshStandardMaterial color="#17212b"/></mesh>
  <gridHelper args={[22,22,"#314150","#202b35"]} position={[0,.015,0]}/>
  <mesh position={[0,2.1,-7]}><boxGeometry args={[22,4,.25]}/><meshStandardMaterial color="#0d151e"/></mesh>
  <mesh position={[-11,2.1,0]}><boxGeometry args={[.25,4,14]}/><meshStandardMaterial color="#0d151e"/></mesh>
  <mesh position={[11,2.1,0]}><boxGeometry args={[.25,4,14]}/><meshStandardMaterial color="#0d151e"/></mesh>
  <Zone position={[-5,0,-.2]} size={[8,4]} label="RESEARCH + CREATIVE" accent="#8be3ad"/>
  <Zone position={[5,0,-.2]} size={[8,4]} label="DEVELOPMENT + QA" accent="#8fd4ff"/>
  <Zone position={[0,0,4.9]} size={[12,3.2]} label="MEETING / OPERATIONS" accent="#ffe18a"/>
  {agents.map(a=><React.Fragment key={a.id}><Desk position={a.desk} name={a.name} accent={a.accent}/><Character agent={a} selected={selected===a.id} onSelect={()=>setSelected(a.id)}/></React.Fragment>)}
  <group position={[8,0,5]}><mesh position={[0,.65,0]}><boxGeometry args={[2,.12,1.2]}/><meshStandardMaterial color="#536273"/></mesh><Text position={[0,.05,.7]} rotation={[-Math.PI/2,0,0]} fontSize={.15} color="#7b8ea1">SERVER / AI INFRA</Text></group>
  <group position={[-8,0,5]}><mesh position={[0,.55,0]}><cylinderGeometry args={[.65,.7,.12,20]}/><meshStandardMaterial color="#5d4636"/></mesh><mesh position={[0,.95,0]}><cylinderGeometry args={[.14,.18,.7,12]}/><meshStandardMaterial color="#3c4650"/></mesh><Text position={[0,.05,.7]} rotation={[-Math.PI/2,0,0]} fontSize={.15} color="#c3a483">COFFEE</Text></group>
 </group>
}

function CameraRig({focus}:{focus:string|null}){
 const {camera}=useThree();
 useEffect(()=>{if(!focus)return;const a=agents.find(x=>x.id===focus);if(!a)return;camera.position.lerp(new THREE.Vector3(a.desk[0]+3,8,a.desk[2]+6),.0);camera.lookAt(a.desk[0],0,a.desk[2]);},[focus,camera]);
 return null;
}

function App(){
 const [selected,setSelected]=useState<string|null>("manager"); const [now,setNow]=useState(new Date()); const [status,setStatus]=useState<any>(null);
 const [chatOpen,setChatOpen]=useState(true);
 const [chatInput,setChatInput]=useState("");
 const [messages,setMessages]=useState<{from:string;text:string;runtimeAction?:any}[]>([{from:"Manager",text:"Studio online hai. Main actual Agent Runtime state read kar raha hoon. Status, queue, bug, ya kisi employee ka naam bolo."}]);
 const sendChat=()=>{const text=chatInput.trim();if(!text)return;const reply=managerReply(text,agents,status);setMessages(m=>[...m,{from:"You",text},{from:agents.find(a=>a.id===reply.agentId)?.name??"Manager",text:reply.text,runtimeAction:reply.runtimeAction}]);setChatInput("");setSelected(reply.agentId);};
 useEffect(()=>{const t=setInterval(()=>setNow(new Date()),1000);return()=>clearInterval(t)},[]);
 useEffect(()=>{fetch("./status.json?ts="+Date.now()).then(r=>r.ok?r.json():null).then(setStatus).catch(()=>{})},[]);
 const selectedAgent=agents.find(a=>a.id===selected)??agents[0];
 const counts=useMemo(()=>({working:agents.filter(a=>a.status==="WORKING").length,active:agents.filter(a=>a.status!=="IDLE").length}),[]);
 return <div className="app">
  <header className="topbar3d"><div className="brand3d"><div className="brandmark">✦</div><div><b>AI AGENT WORKSPACE</b><span>Web Controller • Living Operations Office</span></div></div><div className="topstats"><span><i className="dot green"/> {counts.working} Working</span><span><i className="dot blue"/> {counts.active} Active</span><span className="system">● SYSTEM {status?.ok===false?"ATTENTION":"ONLINE"}</span><span className="clock">{now.toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})}</span></div></header>
  <div className="workspace">
   <aside className="sidebar"><div className="side-title">AGENTS <small>{agents.length}</small></div>{agents.map(a=><button className={"agent-row "+(selected===a.id?"selected":"")} key={a.id} onClick={()=>setSelected(a.id)}><span className="mini-avatar" style={{background:a.color}}>{a.icon}</span><span><b>{a.name}</b><small>{a.role}</small></span><em style={{color:statusTone(a.status)}}>●</em></button>)}<div className="legend"><b>LIVE OFFICE</b><p>Characters move through real destinations and show their current work state.</p><button onClick={()=>setSelected(null)}>View Whole Office</button></div></aside>
   <main className="scene"><Canvas shadows camera={{position:[15,13,15],fov:42}} dpr={[1,1.6]}><color attach="background" args={["#07111c"]}/><ambientLight intensity={1.3}/><directionalLight castShadow position={[4,12,5]} intensity={2.1} shadow-mapSize={[1024,1024]}/><pointLight position={[-7,5,-2]} color="#7dd3fc" intensity={10} distance={13}/><pointLight position={[7,4,3]} color="#c084fc" intensity={8} distance={11}/><Office selected={selected} setSelected={setSelected}/><CameraRig focus={selected}/><OrbitControls makeDefault minPolarAngle={.48} maxPolarAngle={1.18} minDistance={9} maxDistance={25} target={[0,0,0]} enableDamping/></Canvas>
    <div className="scene-title"><b>AI AGENT WORKSPACE</b><span>Isometric Operations Floor</span></div>
    <div className="scene-controls"><button onClick={()=>setSelected("manager")}>⌖ Focus Agent</button><button onClick={()=>setSelected(null)}>◎ Overview</button></div>
    <div className="activity"><b>LIVE ACTIVITY</b><span><i className="pulse"/> {selectedAgent.name} — {selectedAgent.task}</span><small>One active site at a time • state-driven workspace</small></div>
    {chatOpen&&<div className="chat-panel">
      <div className="chat-head"><div><b>MANAGER CHAT</b><small>Talk to the Agent Studio team • GitHub Runtime</small></div><button onClick={()=>setChatOpen(false)}>×</button></div>
      <div className="chat-messages">{messages.map((m,i)=><div key={i} className={"chat-msg "+(m.from==="You"?"you":"")}><span>{m.from}</span><p>{m.text}</p>{m.runtimeAction&&<a className="runtime-action" href={m.runtimeAction?`https://github.com/WebControlerAgent/WebControlerAgent.github.io/issues/new?title=${encodeURIComponent("[Agent Runtime] "+m.runtimeAction.action)}&body=${encodeURIComponent("<!-- agent-runtime-command\n"+JSON.stringify(m.runtimeAction,null,2)+"\n-->")}`:"#"} target="_blank" rel="noreferrer">⚡ Send to GitHub Runtime</a>}</div>)}</div>
      <form className="chat-input" onSubmit={e=>{e.preventDefault();sendChat()}}>
        <input value={chatInput} onChange={e=>setChatInput(e.target.value)} placeholder="Ask Manager..." aria-label="Message Manager"/>
        <button type="submit" aria-label="Send message">➤</button>
      </form>
    </div>}
   </main>
   <aside className="inspector"><div className="inspector-head"><span>SELECTED AGENT</span><button onClick={()=>setSelected(null)}>×</button></div><div className="portrait" style={{background:selectedAgent.color}}><span>{selectedAgent.icon}</span><i style={{background:statusTone(selectedAgent.status)}}/></div><h2>{selectedAgent.name}</h2><p>{selectedAgent.role}</p><div className="status-card"><span>STATUS</span><b style={{color:statusTone(selectedAgent.status)}}>● {selectedAgent.status}</b></div><div className="task-card"><span>CURRENT TASK</span><b>{selectedAgent.task}</b></div><div className="detail"><span>Destination</span><b>{selectedAgent.status==="WALKING"?"Moving through office":"Assigned workstation"}</b></div><div className="detail"><span>Workspace</span><b>Agent Studio</b></div><button className="talk" onClick={()=>setChatOpen(true)}>💬 Open employee channel</button><div className="timeline"><b>RECENT ACTIVITY</b><div>● Task started <small>now</small></div><div>● State → {selectedAgent.status} <small>live</small></div><div>● Next checkpoint <small>queued</small></div></div></aside>
  </div>
 </div>
}
createRoot(document.getElementById("root")!).render(<React.StrictMode><App/></React.StrictMode>);
