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
const CAPTAIN_ORBITS=[
 {radius:5.4,arm:0,offset:-.06,height:.12,speed:.95},
 {radius:6.8,arm:1,offset:.05,height:-.10,speed:.82},
 {radius:8.0,arm:2,offset:-.04,height:.16,speed:.74},
 {radius:9.1,arm:3,offset:.04,height:-.14,speed:.66},
 {radius:10.2,arm:0,offset:.03,height:.08,speed:.60},
 {radius:11.3,arm:1,offset:-.03,height:-.06,speed:.54},
 {radius:12.4,arm:2,offset:.02,height:.13,speed:.49},
 {radius:13.6,arm:3,offset:-.02,height:-.12,speed:.45},
 {radius:14.7,arm:0,offset:.01,height:.04,speed:.41}
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
 const ref=useRef<THREE.Group>(null!);const flame=useRef<THREE.Sprite>(null!);const flare=useRef<THREE.Sprite>(null!);const streak=useRef<THREE.Sprite>(null!);
 const flameTexture=useMemo(()=>{
  const canvas=document.createElement("canvas");canvas.width=canvas.height=512;const ctx=canvas.getContext("2d");
  if(ctx){
   const halo=ctx.createRadialGradient(256,256,2,256,256,228);
   halo.addColorStop(0,"rgba(255,255,255,.98)");halo.addColorStop(.08,accent+"ee");halo.addColorStop(.25,accent+"88");halo.addColorStop(.48,color+"38");halo.addColorStop(1,"rgba(0,0,0,0)");
   ctx.fillStyle=halo;ctx.fillRect(0,0,512,512);
   for(let i=0;i<26;i++){
    const a=i/26*Math.PI*2,inner=78+(i%4)*10,reach=140+(i*37%100),bend=Math.sin(i*2.17)*42;
    const x1=256+Math.cos(a)*inner,y1=256+Math.sin(a)*inner,x2=256+Math.cos(a)*reach,y2=256+Math.sin(a)*reach;
    const mx=(x1+x2)/2+Math.cos(a+Math.PI/2)*bend,my=(y1+y2)/2+Math.sin(a+Math.PI/2)*bend;
    const g=ctx.createLinearGradient(x1,y1,x2,y2);g.addColorStop(0,"rgba(255,255,255,.9)");g.addColorStop(.25,accent+"cc");g.addColorStop(.68,color+"70");g.addColorStop(1,"rgba(0,0,0,0)");
    ctx.beginPath();ctx.moveTo(x1,y1);ctx.quadraticCurveTo(mx,my,x2,y2);ctx.strokeStyle=g;ctx.lineWidth=3+(i%4)*1.8;ctx.lineCap="round";ctx.stroke();
   }
   const core=ctx.createRadialGradient(256,256,0,256,256,86);core.addColorStop(0,"#ffffff");core.addColorStop(.2,"#ffffff");core.addColorStop(.43,accent+"ff");core.addColorStop(.72,color+"88");core.addColorStop(1,"rgba(0,0,0,0)");
   ctx.fillStyle=core;ctx.fillRect(168,168,176,176);
  }
  const t=new THREE.CanvasTexture(canvas);t.colorSpace=THREE.SRGBColorSpace;return t;
 },[accent,color]);
 const flareTexture=useMemo(()=>{
  const canvas=document.createElement("canvas");canvas.width=canvas.height=512;const ctx=canvas.getContext("2d");
  if(ctx){
   const glow=ctx.createRadialGradient(256,256,1,256,256,235);glow.addColorStop(0,"rgba(255,255,255,1)");glow.addColorStop(.035,"rgba(255,255,255,1)");glow.addColorStop(.075,accent+"ff");glow.addColorStop(.16,accent+"bb");glow.addColorStop(.32,accent+"55");glow.addColorStop(.58,accent+"18");glow.addColorStop(1,"rgba(0,0,0,0)");
   ctx.fillStyle=glow;ctx.fillRect(0,0,512,512);
   const rays=[[256,28,256,484,.4,2.2],[28,256,484,256,.4,2.2],[64,64,448,448,.2,1.2],[64,448,448,64,.2,1.2]];
   for(const [x1,y1,x2,y2,alpha,width] of rays){const g=ctx.createLinearGradient(x1,y1,x2,y2);g.addColorStop(0,"rgba(255,255,255,0)");g.addColorStop(.42,"rgba(255,255,255,0)");g.addColorStop(.495,"rgba(255,255,255,"+alpha+")");g.addColorStop(.505,"rgba(255,255,255,"+alpha+")");g.addColorStop(.58,"rgba(255,255,255,0)");g.addColorStop(1,"rgba(255,255,255,0)");ctx.strokeStyle=g;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();}
  }
  const t=new THREE.CanvasTexture(canvas);t.colorSpace=THREE.SRGBColorSpace;return t;
 },[accent]);
 useEffect(()=>()=>{flameTexture.dispose();flareTexture.dispose()},[flameTexture,flareTexture]);
 useFrame(({clock},delta)=>{ref.current.rotation.y+=delta*.12;ref.current.rotation.z+=delta*.035;const t=clock.elapsedTime;
  if(flame.current){const p=1+Math.sin(t*2.2)*.045;flame.current.scale.set(2.15*p,2.45/p,1);flame.current.material.opacity=.42+Math.sin(t*2.2)*.055;}
  if(flare.current){const p=1+Math.sin(t*1.8)*.025;flare.current.scale.set(2.55*p,2.55*p,1);flare.current.material.opacity=.48+Math.sin(t*1.8)*.025;}
  if(streak.current){const p=1+Math.sin(t*1.4+.7)*.02;streak.current.scale.set(3.3*p,.48/p,1);streak.current.material.opacity=.15+Math.sin(t*1.4+.7)*.02;}
 });
 return <group ref={ref} scale={scale}>
  <sprite ref={flame} scale={[2.15,2.45,1]} renderOrder={4}><spriteMaterial map={flameTexture} color="#ffffff" transparent opacity={.42} blending={THREE.AdditiveBlending} depthWrite={false} depthTest={false} toneMapped={false}/></sprite>
  <sprite ref={streak} scale={[3.3,.48,1]} renderOrder={5}><spriteMaterial map={flareTexture} color="#ffffff" transparent opacity={.15} blending={THREE.AdditiveBlending} depthWrite={false} depthTest={false} toneMapped={false}/></sprite>
  <sprite ref={flare} scale={[2.55,2.55,1]} renderOrder={6}><spriteMaterial map={flareTexture} color="#ffffff" transparent opacity={.48} blending={THREE.AdditiveBlending} depthWrite={false} depthTest={false} toneMapped={false}/></sprite>
  <mesh><sphereGeometry args={[.25,48,48]}/><meshBasicMaterial color="#ffffff" toneMapped={false}/></mesh>
  <mesh scale={1.45}><sphereGeometry args={[.27,40,40]}/><meshBasicMaterial color={color} transparent opacity={.32} blending={THREE.AdditiveBlending} depthWrite={false}/></mesh>
 </group>;
}
function CaptainSun({item,index,onSelect,selected}:{item:any;index:number;onSelect:()=>void;selected:boolean}){
 const group=useRef<THREE.Group>(null!);const phase=index*(Math.PI*2/9);const palette=STAR_PALETTE[index];const orbit=CAPTAIN_ORBITS[index];
 useFrame(({clock},delta)=>{
  const t=clock.elapsedTime;
  const radius=orbit.radius+Math.sin(t*.11+phase)*.025;
  const angle=orbit.arm*(Math.PI/2)+2.05*Math.log(radius/1.2)+orbit.offset+t*.0015+Math.sin(t*.09+phase)*.012;
  const x=Math.cos(angle)*radius,z=Math.sin(angle)*radius;
  group.current.position.set(x,orbit.height-x*.1-z*.28+Math.sin(t*.16+phase)*.035,z);
  group.current.rotation.y+=delta*.08;
 });
 return <group ref={group} onClick={(e)=>{e.stopPropagation();onSelect()}}>
  <pointLight color={palette.color} intensity={selected?5.2:2.1} distance={selected?8:5.5} decay={2}/>
  <StarGlow color={palette.color} accent={palette.accent} scale={selected?1.12:.9}/>
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
  const smooth=(t:number)=>t*t*(3-2*t);
  const make=(coreHex:string,midHex:string,outerHex:string,seed:number)=>{
   const size=384;
   const canvas=document.createElement("canvas");canvas.width=canvas.height=size;
   const ctx=canvas.getContext("2d");
   const core=new THREE.Color(coreHex),mid=new THREE.Color(midHex),outer=new THREE.Color(outerHex);
   const hash=(x:number,y:number,s:number)=>{const v=Math.sin(x*127.1+y*311.7+s*74.7)*43758.5453;return v-Math.floor(v)};
   const grids=[5,10,20,40].map((n,layer)=>({n,data:Array.from({length:n*n},(_,i)=>hash(i%n,Math.floor(i/n),seed+layer*19))}));
   const sample=(grid:{n:number;data:number[]},u:number,v:number)=>{
    const x=u*(grid.n-1),y=v*(grid.n-1),x0=Math.floor(x),y0=Math.floor(y),x1=Math.min(grid.n-1,x0+1),y1=Math.min(grid.n-1,y0+1);
    const tx=smooth(x-x0),ty=smooth(y-y0),at=(xx:number,yy:number)=>grid.data[yy*grid.n+xx];
    const a=at(x0,y0)*(1-tx)+at(x1,y0)*tx,b=at(x0,y1)*(1-tx)+at(x1,y1)*tx;
    return a*(1-ty)+b*ty;
   };
   if(ctx){
    const image=ctx.createImageData(size,size);
    for(let y=0;y<size;y++)for(let x=0;x<size;x++){
     const u=x/(size-1),v=y/(size-1),dx=(u-.5)*2,dy=(v-.5)*2;
     const radius=Math.sqrt(dx*dx*.76+dy*dy*1.35);
     const warpU=u+Math.sin(v*9+seed)*.035+Math.sin(v*23+seed*2)*.012;
     const warpV=v+Math.sin(u*8-seed)*.025;
     const n0=sample(grids[0],warpU,warpV),n1=sample(grids[1],warpU,warpV),n2=sample(grids[2],warpU,warpV),n3=sample(grids[3],warpU,warpV);
     const fbm=n0*.43+n1*.28+n2*.19+n3*.10;
     const angle=Math.atan2(dy,dx);
     const filament=.5+.5*Math.sin(angle*4.2+radius*17+fbm*5+seed);
     const envelope=Math.max(0,1-radius*.96);
     const threshold=Math.max(0,(fbm-.29)/.71);
     const density=Math.pow(threshold,1.32)*envelope*(.58+.42*filament);
     const center=Math.max(0,Math.min(1,(.72-radius)*1.65))*Math.max(0,Math.min(1,(fbm-.38)*2.2));
     const t=Math.max(0,Math.min(1,(fbm-.30)*2.1));
     const r0=outer.r*(1-t)+mid.r*t,g0=outer.g*(1-t)+mid.g*t,b0=outer.b*(1-t)+mid.b*t;
     const idx=(y*size+x)*4;
     image.data[idx]=Math.round((r0*(1-center)+core.r*center)*255);
     image.data[idx+1]=Math.round((g0*(1-center)+core.g*center)*255);
     image.data[idx+2]=Math.round((b0*(1-center)+core.b*center)*255);
     image.data[idx+3]=Math.round(Math.min(.72,Math.pow(density,1.12)*.82)*255);
    }
    ctx.putImageData(image,0,0);
    // Fine, irregular filaments break up the cloud silhouette so it reads as gas, not a smooth orb.
    for(let i=0;i<34;i++){
     const angle=i*2.399+seed*.8,reach=55+((i*47+seed*17)%145),start=18+((i*23+seed*7)%72);
     const x=size/2+Math.cos(angle)*start,y=size/2+Math.sin(angle)*start;
     const ex=size/2+Math.cos(angle+.18*Math.sin(i+seed))*reach,ey=size/2+Math.sin(angle+.18*Math.sin(i+seed))*reach;
     const bend=Math.sin(i*1.71+seed)*24;
     const grad=ctx.createLinearGradient(x,y,ex,ey);
     grad.addColorStop(0,"rgba(255,255,255,0)");grad.addColorStop(.38,midHex+"88");grad.addColorStop(.76,outerHex+"55");grad.addColorStop(1,"rgba(0,0,0,0)");
     ctx.beginPath();ctx.moveTo(x,y);ctx.quadraticCurveTo((x+ex)/2-Math.sin(angle)*bend,(y+ey)/2+Math.cos(angle)*bend,ex,ey);
     ctx.strokeStyle=grad;ctx.globalAlpha=.12+((i*13+seed)%5)*.025;ctx.lineWidth=1+(i%4)*1.25;ctx.stroke();
    }
    ctx.globalAlpha=1;
   }
   const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;texture.needsUpdate=true;return texture;
  };
  return [
   make("#fff0b4","#ff9d43","#c63e2d",1),
   make("#d8f7ff","#46c8ff","#3946d9",2),
   make("#ffe0f1","#ff4fa8","#8239e9",3),
   make("#d7fff8","#46e2d2","#3159d8",4)
  ];
 },[]);
 const clouds=useMemo(()=>Array.from({length:46},(_,i)=>{
  const arm=i%4,step=Math.floor(i/4),r=3.0+(step%12)*1.04+(i%3)*.19;
  const angle=arm*(Math.PI/2)+2.05*Math.log(r/1.2)+Math.sin(i*12.9898)*(.055+.18/r);
  return {
   position:[Math.cos(angle)*r,Math.sin(i*2.1)*(.18+r*.012),Math.sin(angle)*r] as [number,number,number],
   scale:[3.0+(i%4)*.88,1.15+(i%3)*.44,1] as [number,number,number],
   texture:i%4,rotation:(angle+Math.PI/2)*.22+(i%3)*.16,phase:i*.73
  };
 }),[]);
 useEffect(()=>()=>textures.forEach(t=>t.dispose()),[textures]);
 useFrame(({clock})=>{
  const t=clock.elapsedTime;
  sprites.current.forEach((sprite,i)=>{
   if(!sprite)return;
   const cloud=clouds[i];
   sprite.material.rotation=cloud.rotation+Math.sin(t*.045+cloud.phase)*.025;
   sprite.material.opacity=.56+Math.sin(t*.12+cloud.phase)*.045;
  });
 });
 return <group>
  {clouds.map((cloud,i)=><sprite key={i} ref={el=>{if(el)sprites.current[i]=el;}} position={cloud.position} rotation={[-Math.PI/2,0,cloud.rotation]} scale={cloud.scale} renderOrder={2}>
   <spriteMaterial map={textures[cloud.texture]} transparent opacity={.56} blending={THREE.AdditiveBlending} depthWrite={false} depthTest={true} toneMapped={false}/>
  </sprite>)}
 </group>;
}
function SpiralGalaxy(){
 const ref=useRef<THREE.Points>(null!);const cloud=useRef<THREE.Points>(null!);
 const geometry=useMemo(()=>{
  const n=28000,p=new Float32Array(n*3),colours=new Float32Array(n*3);
  const palette=["#347fe8","#64c9ff","#ff75c9","#a96bff","#d9b9ff","#f6d8ff","#ffd5a0"].map(v=>new THREE.Color(v));
  for(let i=0;i<n;i++){
   const arm=i%4,r=.42+Math.pow(Math.random(),.76)*15.2,theta=arm*(Math.PI/2)+2.05*Math.log(r/1.2);
   const angularJitter=(Math.random()-.5)*(.12+.42/r),radialJitter=(Math.random()-.5)*(.12+Math.min(.48,r*.025));
   const a=theta+angularJitter,rr=Math.max(.35,r+radialJitter);
   p[i*3]=Math.cos(a)*rr;p[i*3+1]=(Math.random()-.5)*(.035+rr*.014);p[i*3+2]=Math.sin(a)*rr;
   const c=palette[Math.floor(Math.random()*palette.length)],edgeFade=Math.max(.14,1-Math.pow(r/17,1.65)*.76),coreBoost=.62+.38*Math.exp(-r*.22),brightness=(.24+Math.random()*.55)*edgeFade*coreBoost;
   colours[i*3]=c.r*brightness;colours[i*3+1]=c.g*brightness;colours[i*3+2]=c.b*brightness;
  }
  const g=new THREE.BufferGeometry();g.setAttribute("position",new THREE.BufferAttribute(p,3));g.setAttribute("color",new THREE.BufferAttribute(colours,3));return g;
 },[]);
 const cloudGeometry=useMemo(()=>{
  const n=20000,p=new Float32Array(n*3),colours=new Float32Array(n*3);
  const palette=["#e96ac7","#9461e9","#4ca9f0","#55d9e8","#d7a9f0","#e5a6cf"].map(v=>new THREE.Color(v));
  for(let i=0;i<n;i++){
   const arm=i%4,r=1.65+Math.pow(Math.random(),.9)*13.8,theta=arm*(Math.PI/2)+2.05*Math.log(r/1.2),a=theta+(Math.random()-.5)*(.2+.5/r);
   p[i*3]=Math.cos(a)*r;p[i*3+1]=(Math.random()-.5)*(.11+r*.023);p[i*3+2]=Math.sin(a)*r;
   const c=palette[Math.floor(Math.random()*palette.length)],fade=Math.max(.1,1-Math.pow(r/16,1.5)*.82),f=(.2+Math.random()*.42)*fade;
   colours[i*3]=c.r*f;colours[i*3+1]=c.g*f;colours[i*3+2]=c.b*f;
  }
  const g=new THREE.BufferGeometry();g.setAttribute("position",new THREE.BufferAttribute(p,3));g.setAttribute("color",new THREE.BufferAttribute(colours,3));return g;
 },[]);
 useEffect(()=>()=>{geometry.dispose();cloudGeometry.dispose()},[geometry,cloudGeometry]);
 return <group>
  <points ref={cloud} geometry={cloudGeometry}><pointsMaterial size={.24} vertexColors transparent opacity={.68} sizeAttenuation depthWrite={false} blending={THREE.AdditiveBlending} toneMapped={false}/></points>
  <points ref={ref} geometry={geometry}><pointsMaterial size={.082} vertexColors transparent opacity={.94} sizeAttenuation depthWrite={false} blending={THREE.AdditiveBlending} toneMapped={false}/></points>
 </group>;
}
function GalaxySystem(){
 const ref=useRef<THREE.Group>(null!);
 useFrame((_,delta)=>{if(ref.current)ref.current.rotation.y+=delta*.0015});
 return <group ref={ref} rotation={[.28,0,-.1]}><GalaxyNebula/><SpiralGalaxy/></group>;
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
   <Stars radius={100} depth={65} count={12000} factor={1.8} saturation={.7} fade speed={.22}/><GalaxySystem/>
   <CameraTravel mode={system?"system":"universe"} onDone={travelDone}/>
   {!system?<><BlackHole onSelect={exit}/>{CAPTAIN_STARS.map((x,i)=><CaptainSun key={x.id} item={x} index={i} selected={selected===x.id} onSelect={()=>enter(x.id)}/>)}</>:<SolarSystem captain={captain!} onPlanet={setPlanet}/>} 
   <OrbitControls enabled={!traveling} enablePan enableZoom minDistance={system?3:8} maxDistance={system?18:45} dampingFactor={.055} enableDamping/>
  </Canvas>
  {system&&<button className="universe-back" onClick={exit}>← RETURN TO GALAXY</button>}
  {!system&&<a className="gpu-galaxy-link" href="/webgpu-galaxy/" title="Open the experimental GPU-powered galaxy">✦ WEBGPU GALAXY MODE</a>}
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
