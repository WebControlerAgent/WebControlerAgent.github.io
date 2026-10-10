import React,{useEffect,useMemo,useRef,useState} from "react";
import {Canvas,useFrame,useThree} from "@react-three/fiber";
import {OrbitControls,Stars} from "@react-three/drei";
import * as THREE from "three";
import {createRoot} from "react-dom/client";
import "./styles.css";
import {managerReply} from "./chat/managerChat";

type Status="IDLE"|"WALKING"|"WORKING"|"THINKING"|"MEETING"|"SUCCESS"|"ERROR";
type Agent={id:string;name:string;role:string;type:"captain";color:string;accent:string;desk:[number,number,number];waypoints:[number,number,number][];task:string;status:Status;icon:string};
const agents:Agent[]=[
{id:"bug-solver",name:"Bug Solver",role:"Repair Captain",type:"captain",color:"#69435d",accent:"#ff9fbd",desk:[7,0,1.2],waypoints:[[7,0,1.2],[5,0,3],[2,0,4],[7,0,1.2]],task:"Repairing verified defects before retry",status:"WORKING",icon:"F"},

{id:"manager",name:"Manager",role:"Universe Operations Captain",type:"captain",color:"#355c7d",accent:"#7dd3fc",desk:[-7,0,-4],waypoints:[[-7,0,-4],[-2,0,-1],[0,0,2],[-7,0,-4]],task:"Coordinating the active site queue",status:"WORKING",icon:"M"},
{id:"researcher",name:"Researcher",role:"Research Captain",type:"captain",color:"#426b57",accent:"#8be3ad",desk:[-3.5,0,-4],waypoints:[[-3.5,0,-4],[-5,0,1],[-1,0,3],[-3.5,0,-4]],task:"Checking authorized sources",status:"THINKING",icon:"R"},
{id:"image-agent",name:"Image Agent",role:"Media Captain",type:"captain",color:"#6b4c7c",accent:"#d8a7ff",desk:[0,0,-4],waypoints:[[0,0,-4],[4,0,-1],[5,0,2],[0,0,-4]],task:"Preparing approved media assets",status:"WORKING",icon:"I"},
{id:"bug-hunter",name:"Bug Hunter",role:"Diagnostics Captain",type:"captain",color:"#7a5838",accent:"#ffcb7a",desk:[3.5,0,-4],waypoints:[[3.5,0,-4],[5,0,2],[2,0,4],[3.5,0,-4]],task:"Scanning the current build",status:"WALKING",icon:"B"},
{id:"seo-agent",name:"SEO Agent",role:"SEO Captain",type:"captain",color:"#2d6570",accent:"#75e1ed",desk:[7,0,-4],waypoints:[[7,0,-4],[4,0,3],[0,0,3],[7,0,-4]],task:"Optimizing discoverability signals",status:"WORKING",icon:"S"},
{id:"idea-builder",name:"Idea Builder",role:"Innovation Captain",type:"captain",color:"#806b32",accent:"#ffe18a",desk:[-4.8,0,4],waypoints:[[-4.8,0,4],[-1,0,5],[1,0,2],[-4.8,0,4]],task:"Developing the next site concept",status:"THINKING",icon:"N"},
{id:"publisher",name:"Publisher",role:"Publishing Captain",type:"captain",color:"#315d77",accent:"#8fd4ff",desk:[0,0,4],waypoints:[[0,0,4],[5,0,4],[6,0,1],[0,0,4]],task:"Preparing a verified deployment",status:"WORKING",icon:"P"},
{id:"qa",name:"QA Agent",role:"Quality Captain",type:"captain",color:"#35665c",accent:"#8df0c2",desk:[4.8,0,4],waypoints:[[4.8,0,4],[2,0,1],[-2,0,1],[4.8,0,4]],task:"Running final verification checks",status:"SUCCESS",icon:"Q"}
];

const statusTone=(s:Status)=>({IDLE:"#718096",WALKING:"#60a5fa",WORKING:"#4ade80",THINKING:"#c084fc",MEETING:"#fbbf24",SUCCESS:"#34d399",ERROR:"#fb7185"}[s]);


const CAPTAIN_STARS=[
{id:"bug-solver",name:"Repair",color:"#ffb36b",accent:"#ffd9a0"},
{id:"manager",name:"Operations",color:"#fff1a8",accent:"#fff8d0"},
{id:"researcher",name:"Research",color:"#9fd8ff",accent:"#d8f1ff"},
{id:"image-agent",name:"Media",color:"#caa7ff",accent:"#eadcff"},
{id:"bug-hunter",name:"Diagnostics",color:"#ff9b73",accent:"#ffd0bf"},
{id:"seo-agent",name:"SEO",color:"#7de3d1",accent:"#c9fff4"},
{id:"idea-builder",name:"Innovation",color:"#ffe27a",accent:"#fff4bd"},
{id:"publisher",name:"Publishing",color:"#8fc7ff",accent:"#d9edff"},
{id:"qa",name:"Quality",color:"#a5f0b6",accent:"#ddffe5"}
];
const ORBIT_PERIOD_HOURS=12;
const CAPTAIN_ORBITS=[
 {radius:6.6,tilt:.22,speed:1.00},{radius:7.5,tilt:-.31,speed:.88},{radius:8.5,tilt:.10,speed:.76},
 {radius:9.5,tilt:-.42,speed:.68},{radius:10.5,tilt:.28,speed:.61},{radius:11.5,tilt:-.18,speed:.55},
 {radius:12.5,tilt:.36,speed:.50},{radius:13.5,tilt:-.27,speed:.46},{radius:14.5,tilt:.16,speed:.42}
];

const TEAM_TEMPLATES:Record<string,string[]>={
  "bug-solver":["patch-agent","test-agent","security-reviewer","rollback-planner","repair-reviewer"],
  "manager":["planner","scheduler","policy-checker","state-keeper","reporter"],
  "researcher":["source-discovery","fact-checker","analyst","trend-researcher","research-reviewer"],
  "image-agent":["source-validator","asset-preparer","metadata-writer","rights-checker","media-reviewer"],
  "bug-hunter":["log-analyzer","reproduction-agent","root-cause-analyst","regression-planner","diagnostic-reviewer"],
  "seo-agent":["keyword-researcher","metadata-worker","internal-link-worker","sitemap-worker","indexing-diagnostics"],
  "idea-builder":["idea-researcher","opportunity-analyst","prototype-planner","experiment-agent","idea-reviewer"],
  "publisher":["content-builder","frontend-worker","release-worker","deployment-checker","rollback-worker"],
  "qa":["functional-tester","ui-tester","seo-tester","performance-tester","release-gatekeeper"]
};
const prettyTeamName=(id:string)=>id.split("-").map(x=>x.charAt(0).toUpperCase()+x.slice(1)).join(" ");
const PLANET_DATA=[
 {color:"#8d9aaa",accent:"#dbe4ed",size:.17,rough:.86,ring:false},
 {color:"#b78e68",accent:"#e5c39b",size:.20,rough:.72,ring:true},
 {color:"#66899a",accent:"#b9e2ed",size:.19,rough:.68,ring:false},
 {color:"#9c7f72",accent:"#d9b6a7",size:.22,rough:.82,ring:false},
 {color:"#8c8a82",accent:"#d2d0c7",size:.24,rough:.9,ring:false}
];
const STAR_PALETTE=[
 {color:"#ff6b32",accent:"#ffc078"},
 {color:"#ffd24a",accent:"#fff2ad"},
 {color:"#3baeff",accent:"#b9eaff"},
 {color:"#a879ff",accent:"#e1caff"},
 {color:"#ff424f",accent:"#ffb0a8"},
 {color:"#38e2d2",accent:"#b6fff7"},
 {color:"#ffe45c",accent:"#fff8c4"},
 {color:"#8a70ff",accent:"#d3c7ff"},
 {color:"#82ed62",accent:"#d7ffb8"}
];
function StarGlow({color,accent,scale=1}:{color:string;accent:string;scale?:number}){
 const ref=useRef<THREE.Group>(null!);
 const flare=useRef<THREE.Sprite>(null!);
 const streak=useRef<THREE.Sprite>(null!);
 const flareTexture=useMemo(()=>{
   const canvas=document.createElement("canvas");canvas.width=canvas.height=512;
   const ctx=canvas.getContext("2d");
   if(ctx){
     const glow=ctx.createRadialGradient(256,256,1,256,256,235);
     glow.addColorStop(0,"rgba(255,255,255,1)");
     glow.addColorStop(.035,"rgba(255,255,255,1)");
     glow.addColorStop(.075,accent+"ff");
     glow.addColorStop(.16,accent+"bb");
     glow.addColorStop(.32,accent+"55");
     glow.addColorStop(.58,accent+"18");
     glow.addColorStop(1,"rgba(0,0,0,0)");
     ctx.fillStyle=glow;ctx.fillRect(0,0,512,512);
     // Long, tapered diffraction spikes give each captain a crisp celestial silhouette.
     const rays=[[256,5,256,507,1,4.2],[5,256,507,256,1,4.2],[35,35,477,477,.86,2.4],[35,477,477,35,.86,2.4],[175,4,337,508,.62,1.5],[4,175,508,337,.62,1.5],[337,4,175,508,.62,1.5],[508,175,4,337,.62,1.5]];
     for(const [x1,y1,x2,y2,alpha,width] of rays){
       const g=ctx.createLinearGradient(x1,y1,x2,y2);
       g.addColorStop(0,"rgba(255,255,255,0)");g.addColorStop(.42,"rgba(255,255,255,0)");
       g.addColorStop(.495,"rgba(255,255,255,"+alpha+")");g.addColorStop(.505,"rgba(255,255,255,"+alpha+")");
       g.addColorStop(.58,"rgba(255,255,255,0)");g.addColorStop(1,"rgba(255,255,255,0)");
       ctx.strokeStyle=g;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();
     }
     const cross=ctx.createRadialGradient(256,256,0,256,256,58);
     cross.addColorStop(0,"rgba(255,255,255,1)");cross.addColorStop(.22,"rgba(255,255,255,.98)");
     cross.addColorStop(.48,accent+"ff");cross.addColorStop(1,accent+"00");
     ctx.fillStyle=cross;ctx.fillRect(198,198,116,116);
   }
   const t=new THREE.CanvasTexture(canvas);t.colorSpace=THREE.SRGBColorSpace;return t;
 },[accent]);
 useEffect(()=>()=>flareTexture.dispose(),[flareTexture]);
 useFrame(({clock},delta)=>{
   ref.current.rotation.y+=delta*.22;ref.current.rotation.z+=delta*.07;
   const t=clock.elapsedTime;
   if(flare.current){const p=1+Math.sin(t*2.4)*.09;flare.current.scale.set(5.6*p,5.6*p,1);flare.current.material.opacity=.9+Math.sin(t*2.4)*.07;}
   if(streak.current){const p=1+Math.sin(t*1.7+.7)*.08;streak.current.scale.set(7.4*p,1.12/p,1);streak.current.material.opacity=.36+Math.sin(t*1.7+.7)*.07;}
 });
 return <group ref={ref} scale={scale}>
   <sprite ref={streak} scale={[7.4,1.12,1]} renderOrder={5}><spriteMaterial map={flareTexture} color="#ffffff" transparent opacity={.36} blending={THREE.AdditiveBlending} depthWrite={false} depthTest={false} toneMapped={false}/></sprite>
   <sprite ref={flare} scale={[5.6,5.6,1]} renderOrder={6}><spriteMaterial map={flareTexture} color="#ffffff" transparent opacity={.9} blending={THREE.AdditiveBlending} depthWrite={false} depthTest={false} toneMapped={false}/></sprite>
   <mesh><sphereGeometry args={[.25,48,48]}/><meshBasicMaterial color="#ffffff" toneMapped={false}/></mesh>
   <mesh scale={1.45}><sphereGeometry args={[.27,40,40]}/><meshBasicMaterial color={accent} transparent opacity={.72} blending={THREE.AdditiveBlending} depthWrite={false}/></mesh>
   <mesh rotation={[Math.PI/2,.25,0]}><torusGeometry args={[.58,.014,8,128]}/><meshBasicMaterial color={accent} transparent opacity={.7} blending={THREE.AdditiveBlending} depthWrite={false}/></mesh>
   <mesh rotation={[Math.PI/2,-.4,.8]}><torusGeometry args={[.72,.008,8,128]}/><meshBasicMaterial color={color} transparent opacity={.42} blending={THREE.AdditiveBlending} depthWrite={false}/></mesh>
 </group>;
}
function CaptainSun({item,index,onSelect,selected}:{item:any;index:number;onSelect:()=>void;selected:boolean}){
 const group=useRef<THREE.Group>(null!); const phase=index*(Math.PI*2/9); const palette=STAR_PALETTE[index]; const orbit=CAPTAIN_ORBITS[index];
 useFrame(({clock},delta)=>{
   const angle=phase+(clock.elapsedTime/(ORBIT_PERIOD_HOURS*3600))*Math.PI*2*orbit.speed;
   group.current.position.set(Math.cos(angle)*orbit.radius,Math.sin(angle+orbit.tilt)*(.55+index*.035),Math.sin(angle)*orbit.radius);
   group.current.rotation.y+=delta*.12;
 });
 return <group ref={group} onClick={(e)=>{e.stopPropagation();onSelect()}}>
   <pointLight color={palette.color} intensity={selected?7:3.2} distance={7.5} decay={2}/>
   <StarGlow color={palette.color} accent={palette.accent} scale={selected?1.3:1.05}/>
   <mesh rotation={[Math.PI/2,0,0]}><torusGeometry args={[.82,.018,10,128]}/><meshBasicMaterial color={palette.accent} transparent opacity={selected?.72:.34} blending={THREE.AdditiveBlending}/></mesh>
   <mesh rotation={[Math.PI/2,.2,.45]}><torusGeometry args={[.7,.035,10,96]}/><meshBasicMaterial color={palette.color} transparent opacity={.28} blending={THREE.AdditiveBlending}/></mesh>
   <mesh rotation={[Math.PI/2,0,.8]}><torusGeometry args={[1.05,.008,8,128]}/><meshBasicMaterial color={palette.color} transparent opacity={selected?.26:.1} blending={THREE.AdditiveBlending}/></mesh>
   {selected&&<mesh rotation={[Math.PI/2,0,0]}><torusGeometry args={[1.24,.014,10,128]}/><meshBasicMaterial color={palette.accent} transparent opacity={.72} blending={THREE.AdditiveBlending}/></mesh>}
 </group>;
}
function BlackHole({onSelect}:{onSelect:()=>void}){
 const ref=useRef<THREE.Group>(null!); const disk=useRef<THREE.Group>(null!);
 const inner=useRef<THREE.Mesh>(null!);const halo=useRef<THREE.Mesh>(null!);
 useFrame(({clock},delta)=>{
   ref.current.rotation.y+=delta*.025;
   disk.current.rotation.z-=delta*.18;
   if(inner.current){const p=1+Math.sin(clock.elapsedTime*2.1)*.035;inner.current.scale.setScalar(p);}
   if(halo.current){const p=1+Math.sin(clock.elapsedTime*1.2)*.045;halo.current.scale.setScalar(p);}
 });
 return <group ref={ref} onClick={(e)=>{e.stopPropagation();onSelect()}}>
   <pointLight color="#ff7438" intensity={5.5} distance={15} decay={1.8}/>
   <pointLight color="#8a58ff" intensity={3.5} distance={13} decay={2}/>
   <mesh ref={halo} scale={1.8}><sphereGeometry args={[1.08,48,48]}/><meshBasicMaterial color="#5421a0" transparent opacity={.12} blending={THREE.AdditiveBlending} depthWrite={false}/></mesh>
   <mesh ref={inner} scale={1.35}><sphereGeometry args={[1.08,64,64]}/><meshBasicMaterial color="#000000"/></mesh>
   <mesh scale={1.11}><sphereGeometry args={[1.08,48,48]}/><meshBasicMaterial color="#010106"/></mesh>
   <group ref={disk}>
     <mesh rotation={[Math.PI/2,0,0]}><torusGeometry args={[1.30,.22,28,192]}/><meshStandardMaterial color="#ff7b28" emissive="#ff4b12" emissiveIntensity={7} roughness={.2} metalness={.04}/></mesh>
     <mesh rotation={[Math.PI/2,0,0]}><torusGeometry args={[1.42,.105,24,192]}/><meshBasicMaterial color="#fff0bb" transparent opacity={.92} blending={THREE.AdditiveBlending} depthWrite={false}/></mesh>
     <mesh rotation={[Math.PI/2,0,0]}><torusGeometry args={[1.63,.075,20,192]}/><meshBasicMaterial color="#ff8a38" transparent opacity={.74} blending={THREE.AdditiveBlending} depthWrite={false}/></mesh>
     <mesh rotation={[Math.PI/2,0,0]}><torusGeometry args={[1.87,.035,16,192]}/><meshBasicMaterial color="#bb6cff" transparent opacity={.43} blending={THREE.AdditiveBlending} depthWrite={false}/></mesh>
     <mesh rotation={[Math.PI/2,0,.32]}><torusGeometry args={[2.16,.014,10,192]}/><meshBasicMaterial color="#568dff" transparent opacity={.2} blending={THREE.AdditiveBlending} depthWrite={false}/></mesh>
     <mesh rotation={[Math.PI/2,.05,.5]}><torusGeometry args={[2.38,.009,8,192]}/><meshBasicMaterial color="#ff75c8" transparent opacity={.16} blending={THREE.AdditiveBlending} depthWrite={false}/></mesh>
   </group>
   <mesh rotation={[Math.PI/2,0,0]}><torusGeometry args={[1.12,.024,12,160]}/><meshBasicMaterial color="#fff8d9" transparent opacity={.86} blending={THREE.AdditiveBlending} depthWrite={false}/></mesh>
   <mesh rotation={[.08,0,.08]} position={[0,2.15,0]}><coneGeometry args={[.19,2.5,24,1,true]}/><meshBasicMaterial color="#ff9a55" transparent opacity={.12} side={THREE.DoubleSide} blending={THREE.AdditiveBlending} depthWrite={false}/></mesh>
   <mesh rotation={[Math.PI-.08,0,.08]} position={[0,-2.15,0]}><coneGeometry args={[.19,2.5,24,1,true]}/><meshBasicMaterial color="#8c6aff" transparent opacity={.1} side={THREE.DoubleSide} blending={THREE.AdditiveBlending} depthWrite={false}/></mesh>
 </group>;
}
function Planet({index,onClick}:{index:number;onClick:()=>void}){
 const ref=useRef<THREE.Group>(null!); const d=PLANET_DATA[index]; const radius=2.0+index*.68; const phase=index*1.25;
 useFrame(({clock},delta)=>{const a=phase+clock.elapsedTime*(.14/(1+index*.42));ref.current.position.set(Math.cos(a)*radius,Math.sin(a*1.7)*(.1+index*.04),Math.sin(a)*radius);ref.current.rotation.y+=delta*(.3+index*.08)});
 return <group ref={ref} onClick={(e)=>{e.stopPropagation();onClick()}}>
   <pointLight color={d.accent} intensity={.035} distance={1}/>
   <mesh castShadow receiveShadow><sphereGeometry args={[d.size,40,40]}/><meshStandardMaterial color={d.color} roughness={d.rough} metalness={.02}/></mesh>
   {d.ring&&<mesh rotation={[Math.PI/2.5,.15,0]}><torusGeometry args={[d.size*1.65,d.size*.12,12,64]}/><meshStandardMaterial color="#cbbda9" roughness={.85} metalness={.02}/></mesh>}
 </group>;
}
function SolarSystem({captain,onPlanet}:{captain:any;onPlanet:(name:string)=>void}){
 const team=TEAM_TEMPLATES[captain.id]??TEAM_TEMPLATES.manager;
 const ref=useRef<THREE.Group>(null!); const palette=STAR_PALETTE[CAPTAIN_STARS.findIndex(x=>x.id===captain.id)];
 useFrame((_,delta)=>{ref.current.rotation.y+=delta*.008});
 return <group ref={ref}>
   <pointLight color={palette.color} intensity={18} distance={18} decay={1.7}/>
   <StarGlow color={palette.color} accent={palette.accent} scale={1.15}/>
   {team.map((name,i)=><React.Fragment key={name}>
     <mesh rotation={[Math.PI/2,0,0]}><torusGeometry args={[2.0+i*.68,.006,6,96]}/><meshBasicMaterial color="#aebdca" transparent opacity={.13}/></mesh>
     <Planet index={i} onClick={()=>onPlanet(name)}/>
   </React.Fragment>)}
 </group>;
}
function CameraTravel({mode,onDone}:{mode:"universe"|"system";onDone:()=>void}){
 const {camera}=useThree();
 const previous=useRef(mode);
 const active=useRef(false);
 const target=useRef(new THREE.Vector3());
 const look=useRef(new THREE.Vector3());
 useEffect(()=>{
   if(previous.current!==mode){
     previous.current=mode;
     active.current=true;
     const timer=window.setTimeout(()=>{active.current=false;onDone()},950);
     return()=>window.clearTimeout(timer);
   }
 },[mode,onDone]);
 useFrame((_,delta)=>{
   if(!active.current)return;
   if(mode==="system"){target.current.set(0,2.0,7.4);look.current.set(0,0,0)}
   else{target.current.set(0,10,22);look.current.set(0,0,0)}
   camera.position.lerp(target.current,1-Math.pow(.001,delta));
   const q=new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().lookAt(camera.position,look.current,camera.up));
   camera.quaternion.slerp(q,1-Math.pow(.001,delta));
 });
 return null;
}
function GalaxyNebula(){
 const sprites=useRef<THREE.Sprite[]>([]);
 const textures=useMemo(()=>{
   const make=(inner:string,mid:string)=>{
     const c=document.createElement("canvas");c.width=c.height=256;const x=c.getContext("2d");
     if(x){const g=x.createRadialGradient(128,128,4,128,128,126);g.addColorStop(0,inner);g.addColorStop(.25,mid);g.addColorStop(.58,"rgba(120,100,255,0.13)");g.addColorStop(1,"rgba(0,0,0,0)");x.fillStyle=g;x.fillRect(0,0,256,256);}
     const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return t;
   };
   return [make("rgba(255,105,202,0.72)","rgba(201,75,255,0.4)"),make("rgba(70,190,255,0.72)","rgba(81,95,255,0.38)"),make("rgba(255,172,222,0.6)","rgba(255,93,151,0.32)")];
 },[]);
 const clouds=useMemo(()=>Array.from({length:12},(_,i)=>{
   const arm=i%5,r=3.4+(i%4)*2.35,angle=arm*Math.PI*2/5+r*.49+(i%3-.8)*.22;
   return {position:[Math.cos(angle)*r,(i%3-1)*.42,Math.sin(angle)*r] as [number,number,number],scale:[3.4+(i%3)*1.2,2.1+(i%4)*.55,1] as [number,number,number],texture:i%3,rotation:angle};
 }),[]);
 useEffect(()=>()=>textures.forEach(t=>t.dispose()),[textures]);
 useFrame(({clock},delta)=>{sprites.current.forEach((sprite,i)=>{if(sprite){sprite.material.rotation=Math.sin(clock.elapsedTime*.13+i)*.12+clouds[i].rotation*.22; sprite.material.opacity=.24+Math.sin(clock.elapsedTime*.35+i*1.7)*.045;}});});
 return <group>{clouds.map((cloud,i)=><sprite key={i} ref={el=>{if(el)sprites.current[i]=el;}} position={cloud.position} scale={cloud.scale} renderOrder={1}><spriteMaterial map={textures[cloud.texture]} transparent opacity={.24} blending={THREE.AdditiveBlending} depthWrite={false} toneMapped={false}/></sprite>)}</group>;
}
function SpiralGalaxy(){
 const ref=useRef<THREE.Points>(null!);const cloud=useRef<THREE.Points>(null!);
 const geometry=useMemo(()=>{
  const n=24000,p=new Float32Array(n*3),colours=new Float32Array(n*3);
  const palette=["#3e9dff","#78d8ff","#ff75bd","#b26dff","#ffb0d2","#f9d5ff","#ffd78a"].map(v=>new THREE.Color(v));
  for(let i=0;i<n;i++){const arm=i%5,r=.55+Math.pow(Math.random(),.72)*15.5,ang=arm*Math.PI*2/5+r*.49+(Math.random()-.5)*(.18+r*.035),spread=(Math.random()-.5)*(.16+r*.026);p[i*3]=Math.cos(ang+spread)*r;p[i*3+1]=(Math.random()-.5)*(.08+r*.012);p[i*3+2]=Math.sin(ang+spread)*r;const q=palette[Math.floor(Math.random()*palette.length)].clone().multiplyScalar(.38+Math.random()*.9);colours[i*3]=q.r;colours[i*3+1]=q.g;colours[i*3+2]=q.b}
  const g=new THREE.BufferGeometry();g.setAttribute("position",new THREE.BufferAttribute(p,3));g.setAttribute("color",new THREE.BufferAttribute(colours,3));return g
 },[]);
 const cloudGeometry=useMemo(()=>{
  const n=9500,p=new Float32Array(n*3),colours=new Float32Array(n*3);const palette=["#ed5aab","#9e62ff","#438cff","#47d9ff","#ffc1df"].map(v=>new THREE.Color(v));
  for(let i=0;i<n;i++){const arm=i%5,r=2.1+Math.random()*12.8,ang=arm*Math.PI*2/5+r*.49+(Math.random()-.5)*(.32+r*.035);p[i*3]=Math.cos(ang)*r;p[i*3+1]=(Math.random()-.5)*(.2+r*.035);p[i*3+2]=Math.sin(ang)*r;const q=palette[Math.floor(Math.random()*palette.length)];const f=.12+Math.random()*.36;colours[i*3]=q.r*f;colours[i*3+1]=q.g*f;colours[i*3+2]=q.b*f}
  const g=new THREE.BufferGeometry();g.setAttribute("position",new THREE.BufferAttribute(p,3));g.setAttribute("color",new THREE.BufferAttribute(colours,3));return g
 },[]);
 useEffect(()=>()=>{geometry.dispose();cloudGeometry.dispose()},[geometry,cloudGeometry]);
 useFrame((_,d)=>{if(ref.current)ref.current.rotation.y+=d*.004;if(cloud.current)cloud.current.rotation.y-=d*.002});
 return <group rotation={[.22,0,-.12]}><points ref={cloud} geometry={cloudGeometry}><pointsMaterial size={.22} vertexColors transparent opacity={.46} sizeAttenuation depthWrite={false} blending={THREE.AdditiveBlending}/></points><points ref={ref} geometry={geometry}><pointsMaterial size={.085} vertexColors transparent opacity={.96} sizeAttenuation depthWrite={false} blending={THREE.AdditiveBlending}/></points><mesh rotation={[Math.PI/2,0,0]}><torusGeometry args={[7.6,.11,8,180]}/><meshBasicMaterial color="#a25dff" transparent opacity={.1} blending={THREE.AdditiveBlending}/></mesh><mesh rotation={[Math.PI/2,0,0]}><torusGeometry args={[10.2,.07,8,180]}/><meshBasicMaterial color="#55aaff" transparent opacity={.09} blending={THREE.AdditiveBlending}/></mesh></group>;
}
function Universe3D({selected,setSelected}:{selected:string|null;setSelected:(id:string|null)=>void}){
 const [system,setSystem]=useState<string|null>(null);
 const [planet,setPlanet]=useState<string|null>(null);
 const [traveling,setTraveling]=useState(false);
 const captain=CAPTAIN_STARS.find(x=>x.id===system);
 const enter=(id:string)=>{setPlanet(null);setTraveling(true);setSystem(id);setSelected(id)};
 const exit=()=>{setPlanet(null);setTraveling(true);setSystem(null);setSelected("manager")};
 const travelDone=useMemo(()=>()=>setTraveling(false),[]);
 return <div className="universe-canvas-wrap">
  <Canvas camera={{position:[0,10,22],fov:48,near:.1,far:1000}} dpr={[1,1.7]} gl={{antialias:true}} shadows>
   <color attach="background" args={["#010208"]}/><fog attach="fog" args={["#010208",28,90]}/><ambientLight intensity={.07}/><directionalLight position={[6,10,4]} intensity={.18}/>
   <Stars radius={100} depth={65} count={12000} factor={1.8} saturation={.7} fade speed={.22}/><GalaxyNebula/><SpiralGalaxy/>
   <CameraTravel mode={system?"system":"universe"} onDone={travelDone}/>
   {!system?<><BlackHole onSelect={exit}/>{CAPTAIN_STARS.map((x,i)=><React.Fragment key={x.id}><mesh rotation={[CAPTAIN_ORBITS[i].tilt,0,i*.35]}><torusGeometry args={[CAPTAIN_ORBITS[i].radius,.006,6,160]}/><meshBasicMaterial color={STAR_PALETTE[i].accent} transparent opacity={.08} blending={THREE.AdditiveBlending}/></mesh><CaptainSun item={x} index={i} selected={selected===x.id} onSelect={()=>enter(x.id)}/></React.Fragment>)}</>:<SolarSystem captain={captain!} onPlanet={setPlanet}/>} 
   <OrbitControls enabled={!traveling} enablePan enableZoom minDistance={system?3:8} maxDistance={system?18:45} dampingFactor={.055} enableDamping/>
  </Canvas>
  {system&&<button className="universe-back" onClick={exit}>← RETURN TO GALAXY</button>}
  {system&&<div className="system-hud"><b>{captain?.name.toUpperCase()} SOLAR SYSTEM</b><span>CAPTAIN STAR • {((TEAM_TEMPLATES[captain?.id??"manager"]??TEAM_TEMPLATES.manager).length)} TEAM PLANETS</span>{planet&&<small>SELECTED PLANET: {prettyTeamName(planet)}</small>}</div>}
 </div>;
}

type SiteRecord={id:string;name:string;repository:string;branch:string;live_url:string;enabled:boolean;authorized:boolean;description?:string;media?:{enabled:boolean;authorized_source:boolean;path:string}};

function SitePanel({sites,selectedSite,setSelectedSite,onClose}:{sites:SiteRecord[];selectedSite:string;setSelectedSite:(id:string)=>void;onClose:()=>void}){
 const [openAdd,setOpenAdd]=useState(false); const [form,setForm]=useState({id:"",name:"",repository:"",branch:"main",live_url:"",description:"",media_path:"chapter-images/"});
 const request=(title:string,command:any)=>{const body="<!-- site-manager-command\\n"+JSON.stringify(command,null,2)+"\\n-->"; const url="https://github.com/WebControlerAgent/WebControlerAgent.github.io/issues/new?title="+encodeURIComponent(title)+"&body="+encodeURIComponent(body); window.open(url,"_blank","noopener,noreferrer");}; const submit=(e:React.FormEvent)=>{e.preventDefault(); if(!form.id||!form.name||!form.repository||!form.live_url)return; request("[Site Manager] Add "+form.name,{action:"add",...form,authorized:true,enabled:true,media_enabled:!!form.media_path}); setOpenAdd(false); };
 return <div className="site-overlay"><div className="site-panel"><div className="site-panel-head"><div><b>SITES CONTROL</b><small>Authorized GitHub targets • one active site at a time</small></div><button onClick={onClose}>×</button></div><div className="site-list">{sites.map(s=><div key={s.id} className={"site-card-wrap "+(selectedSite===s.id?"active":"")}><button className="site-card" onClick={()=>setSelectedSite(s.id)}><span className="site-dot" style={{background:s.enabled&&s.authorized?"#4ade80":"#64748b"}}/><span><b>{s.name}</b><small>{s.repository}</small><small>{s.live_url}</small></span><em>{s.enabled?"ENABLED":"DISABLED"}</em></button><div className="site-card-actions"><button onClick={()=>request("[Agent Runtime] Run "+s.name,{action:"claim",site:s.id})}>▶ Run Pipeline</button><button onClick={()=>request("[Site Manager] "+(s.enabled?"Disable ":"Enable ")+s.name,{action:s.enabled?"disable":"enable",id:s.id})}>{s.enabled?"Disable":"Enable"}</button><button onClick={()=>request("[Site Manager] Remove "+s.name,{action:"remove",id:s.id})}>Remove</button></div></div>)}</div><div className="site-actions"><button onClick={()=>setOpenAdd(v=>!v)}>＋ ADD SITE</button><a href="https://github.com/WebControlerAgent/WebControlerAgent.github.io/issues?q=is%3Aissue+label%3Asite-manager" target="_blank" rel="noreferrer">Open Site Manager</a></div>{openAdd&&<form className="site-form" onSubmit={submit}><b>ADD AUTHORIZED SITE</b><input placeholder="site-id e.g. my-site" value={form.id} onChange={e=>setForm({...form,id:e.target.value.toLowerCase().replace(/[^a-z0-9-]/g,"")})}/><input placeholder="Site name" value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/><input placeholder="GitHub repository owner/name" value={form.repository} onChange={e=>setForm({...form,repository:e.target.value})}/><input placeholder="Branch" value={form.branch} onChange={e=>setForm({...form,branch:e.target.value})}/><input placeholder="Live URL" value={form.live_url} onChange={e=>setForm({...form,live_url:e.target.value})}/><input placeholder="Media path (optional)" value={form.media_path} onChange={e=>setForm({...form,media_path:e.target.value})}/><textarea placeholder="Description" value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/><p>Adding a site creates a protected GitHub Site Manager request. It is not activated until the authorized registry is updated by Actions.</p><button type="submit">Create Site Request →</button></form>}</div></div>;
}

function App(){
 const [selected,setSelected]=useState<string|null>("manager"); const [sites,setSites]=useState<SiteRecord[]>([]); const [selectedSite,setSelectedSite]=useState("kingdom-raw"); const [sitesOpen,setSitesOpen]=useState(false); const [now,setNow]=useState(new Date()); const [status,setStatus]=useState<any>(null);
 const [chatOpen,setChatOpen]=useState(true);
 const runtimeAgents=useMemo(()=>{const raw=status?.agent_runtime?.agent_states??{};return agents.map(a=>({...a,runtimeState:raw[a.id]?.state??null,runtimeSite:raw[a.id]?.site??null,runtimeTask:raw[a.id]?.task??null,runtimeError:raw[a.id]?.error??null}));},[status]);
 const runtimeTone=(state:string|null,fallback:string)=>state==="FAILED"?"#fb7185":state==="REPAIRING"?"#fbbf24":state==="VERIFYING"?"#60a5fa":state==="COMPLETED"?"#34d399":state==="WORKING"?"#4ade80":fallback;
 const runtimeEvents=useMemo(()=>Array.isArray(status?.agent_runtime?.events)?status.agent_runtime.events.slice(-18).reverse():[],[status]);
 const liveEvents=runtimeEvents.filter((e:any)=>e.site===selectedSite || !e.site).slice(0,8);
 const refreshStatus=()=>fetch("./status.json?ts="+Date.now()).then(r=>r.ok?r.json():null).then(setStatus).catch(()=>{});
 const [chatInput,setChatInput]=useState("");
 const [messages,setMessages]=useState<{from:string;text:string;runtimeAction?:any;aiRequest?:string}[]>([{from:"Manager",text:"Studio online hai. Main actual Agent Runtime state read kar raha hoon. Status, queue, bug, ya kisi employee ka naam bolo."}]);
 const sendChat=()=>{const text=chatInput.trim();if(!text)return;const siteName=sites.find(s=>s.id===selectedSite)?.name??selectedSite;const enriched=text+`\\nActive site: ${siteName} (${selectedSite})`;const reply=managerReply(enriched,agents,status);if(reply.runtimeAction&&!reply.runtimeAction.site)reply.runtimeAction.site=selectedSite;setMessages(m=>[...m,{from:"You",text},{from:agents.find(a=>a.id===reply.agentId)?.name??"Manager",text:reply.text,runtimeAction:reply.runtimeAction,aiRequest:reply.aiRequest}]);setChatInput("");setSelected(reply.agentId);};
 useEffect(()=>{const t=setInterval(()=>setNow(new Date()),1000);return()=>clearInterval(t)},[]);
 useEffect(()=>{refreshStatus();fetch("./sites.json?ts="+Date.now()).then(r=>r.ok?r.json():null).then(d=>setSites(d?.sites??[])).catch(()=>{});const t=setInterval(refreshStatus,15000);return()=>clearInterval(t)},[]);
 const selectedAgent=agents.find(a=>a.id===selected)??agents[0];
 const runtimeSelected=runtimeAgents.find(a=>a.id===selectedAgent.id);
 const liveState=runtimeSelected?.runtimeState??null;
 const liveTask=runtimeSelected?.runtimeTask??selectedAgent.task;
 const liveError=runtimeSelected?.runtimeError??null;

 const counts=useMemo(()=>({working:runtimeAgents.filter(a=>a.runtimeState==="WORKING").length,active:runtimeAgents.filter(a=>a.runtimeState && a.runtimeState!=="IDLE").length}),[runtimeAgents]);
 return <div className="app">
  <header className="topbar3d"><div className="brand3d"><div className="brandmark">✦</div><div><b>AIWCU</b><span>Autonomous Instinct Web Controller Universe</span></div></div><div className="topstats"><span><i className="dot green"/> {counts.working} Working</span><span><i className="dot blue"/> {counts.active} Active</span><span className="system">● SYSTEM {status?.ok===false?"ATTENTION":"ONLINE"}</span><span className="clock">{now.toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})}</span></div></header>
  <div className="workspace">
   <aside className="sidebar"><div className="side-title">CAPTAINS <small>{agents.length}</small></div>{runtimeAgents.map(a=><button className={"agent-row "+(selected===a.id?"selected":"")} key={a.id} onClick={()=>setSelected(a.id)}><span className="mini-avatar" style={{background:a.color}}>{a.icon}</span><span><b>{a.name}</b><small>{a.runtimeState??a.status}</small></span><em style={{color:runtimeTone(a.runtimeState,a.accent)}}>●</em></button>)}<div className="legend"><b>LIVE OFFICE</b><p>Characters move through real destinations and show their current work state.</p><button onClick={()=>setSelected(null)}>View Whole Office</button></div></aside>
   <main className="scene"><div className="universe-3d"><Universe3D selected={selected} setSelected={setSelected}/><div className="universe-3d-hud"><b>AIWCU UNIVERSE</b><span>BLACK HOLE • 9 CAPTAIN STARS • 12H ORBIT CYCLE</span><small>Drag to travel • Scroll to zoom • Click a star to select a Captain</small></div><div className="universe-3d-legend"><span>● BLACK HOLE — MANAGER</span><span>✦ CAPTAIN STAR</span></div></div><div className="scene-title"><b>AIWCU</b><span>Autonomous Instinct Web Controller Universe • Galaxy Control</span></div><div className="site-selector"><span>ACTIVE SITE</span><b>{sites.find(s=>s.id===selectedSite)?.name??"Loading sites..."}</b><button onClick={()=>setSitesOpen(true)}>⚙ Sites</button></div>
    <div className="scene-controls"><button onClick={()=>setSelected("manager")}>⌖ Focus Agent</button><button onClick={()=>setSelected(null)}>◎ Overview</button></div>
    <div className="activity"><b>LIVE ACTIVITY</b><span><i className="pulse"/> {selectedAgent.name} — {liveTask}</span><small>{liveState?`Runtime: ${liveState}`:"Waiting for runtime event"} • auto-refresh 15s</small></div>
    {sitesOpen&&<SitePanel sites={sites} selectedSite={selectedSite} setSelectedSite={setSelectedSite} onClose={()=>setSitesOpen(false)}/>} {chatOpen&&<div className="chat-panel">
      <div className="chat-head"><div><b>MANAGER CHAT</b><small>Talk to the selected Captain • GitHub Runtime</small></div><button onClick={()=>setChatOpen(false)}>×</button></div>
      <div className="chat-messages">{messages.map((m,i)=><div key={i} className={"chat-msg "+(m.from==="You"?"you":"")}><span>{m.from}</span><p>{m.text}</p>{m.runtimeAction&&<a className="runtime-action" href={`https://github.com/WebControlerAgent/WebControlerAgent.github.io/issues/new?title=${encodeURIComponent("[Agent Runtime] "+m.runtimeAction.action)}&body=${encodeURIComponent("<!-- agent-runtime-command\n"+JSON.stringify(m.runtimeAction,null,2)+"\n-->")}`} target="_blank" rel="noreferrer">⚡ Send to GitHub Runtime</a>}{m.aiRequest&&<a className="runtime-action" href={`https://github.com/WebControlerAgent/WebControlerAgent.github.io/issues/new?title=${encodeURIComponent("[Manager AI] "+m.aiRequest.slice(0,60))}&body=${encodeURIComponent(m.aiRequest)}`} target="_blank" rel="noreferrer">🧠 Send to Manager AI</a>}</div>)}</div>
      <form className="chat-input" onSubmit={e=>{e.preventDefault();sendChat()}}>
        <input value={chatInput} onChange={e=>setChatInput(e.target.value)} placeholder="Ask Manager..." aria-label="Message Manager"/>
        <button type="submit" aria-label="Send message">➤</button>
      </form>
    </div>}
   </main>
   <aside className="inspector"><div className="inspector-head"><span>SELECTED CAPTAIN</span><button onClick={()=>setSelected(null)}>×</button></div><div className="portrait" style={{background:selectedAgent.color}}><span>{selectedAgent.icon}</span><i style={{background:statusTone(selectedAgent.status)}}/></div><h2>{selectedAgent.name}</h2><p>{selectedAgent.role}</p><div className="status-card"><span>STATUS</span><b style={{color:liveState?runtimeTone(liveState,selectedAgent.accent):statusTone(selectedAgent.status)}}>● {liveState??selectedAgent.status}</b></div><div className="task-card"><span>CURRENT TASK</span><b>{liveTask}</b></div><div className="detail"><span>Destination</span><b>{selectedAgent.status==="WALKING"?"Moving through office":"Assigned workstation"}</b></div><div className="detail"><span>Workspace</span><b>AIWCU Universe</b></div><button className="talk" onClick={()=>setChatOpen(true)}>💬 Open captain channel</button><div className="timeline"><b>RECENT ACTIVITY</b>{liveEvents.length?liveEvents.slice(0,5).map((e:any,i:number)=><div className="timeline-event" key={i}><span>● {(e.type||"event").replaceAll("_"," ")}{e.task?": "+e.task:""}</span><small>{e.at?new Date(e.at).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"}):"live"}</small></div>):<><div>● Current state → {liveState??selectedAgent.status} <small>live</small></div><div>● Task → {liveTask} <small>live</small></div><div>● Next checkpoint <small>queued</small></div></>}{liveError&&<div className="runtime-error">⚠ {liveError}</div>}</div></aside>
  </div>
 </div>
}
createRoot(document.getElementById("root")!).render(<App/>);
window.dispatchEvent(new Event("agent-app-ready"));
