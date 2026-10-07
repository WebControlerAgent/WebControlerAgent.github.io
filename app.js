const $=id=>document.getElementById(id);
const state={lastRun:localStorage.getItem("lastRun")||"—",runs:Number(localStorage.getItem("runs")||0)};
function render(){ $("controller").textContent="Ready"; $("lastRun").textContent=state.lastRun; $("repos").textContent="Configured via Actions"; $("status").textContent="● Ready"; }
$("refresh").onclick=()=>{render();$("message").textContent="Dashboard refreshed."};
$("run").onclick=()=>{state.runs++;state.lastRun=new Date().toLocaleString();localStorage.setItem("lastRun",state.lastRun);localStorage.setItem("runs",state.runs);render();$("message").textContent="Manual request queued. GitHub Actions performs the server-side work."; $("log").textContent=new Date().toISOString()+"  manual monitor request\n"+$("log").textContent};
render();