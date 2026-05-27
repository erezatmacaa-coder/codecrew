import asyncio
import json
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
from masa.core import Orchestrator
from masa.agents import AGENTS

app = FastAPI(title="CodeCrew")

HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CodeCrew - Erez'in Ofisi</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background: #0a0a1a; color: #e0e0e0; font-family: 'Courier New', monospace;
         display: flex; justify-content: center; padding: 10px; overflow-x: hidden; }
  .game-wrap { max-width: 840px; width: 100%; }
  .top-bar { display:flex; justify-content:space-between; align-items:center;
             padding:8px 0; }
  .top-bar h1 { font-size:18px; color:#ffe66d; text-shadow:0 0 10px #ffe66d44; }
  .top-bar span { font-size:12px; color:#4ecdc4; }
  canvas { display:block; margin:0 auto; border:2px solid #30363d; border-radius:6px;
           image-rendering:pixelated; width:100%; max-width:800px; background:#16213e; }
  .panel { background:#0f3460ee; border:2px solid #30363d; border-top:none;
           padding:12px; border-radius:0 0 10px 10px; }
  .task-row { display:flex; gap:8px; }
  .task-row input { flex:1; padding:10px 14px; border-radius:6px;
                    border:1px solid #30363d; background:#16213e; color:#e0e0e0;
                    font-size:14px; font-family:inherit; }
  .task-row input:focus { outline:none; border-color:#ffe66d; }
  .task-row button { padding:10px 24px; border-radius:6px; border:none;
                     background:#ffe66d; color:#0a0a1a; font-size:14px;
                     cursor:pointer; font-weight:bold; font-family:inherit; }
  .task-row button:hover { background:#fff3a0; }
  .task-row button:disabled { opacity:0.4; cursor:not-allowed; }
  #log { margin-top:10px; max-height:180px; overflow-y:auto; padding:8px;
         background:#16213e; border-radius:4px; font-size:12px; line-height:1.5;
         display:none; }
  .log-msg { padding:3px 0; border-bottom:1px solid #1a1a2e; }
  .monitor { display:flex; gap:6px; flex-wrap:wrap; margin-top:8px;
             font-size:11px; color:#8892b0; }
  .monitor span { padding:2px 8px; border-radius:10px; background:#16213e;
                  border:1px solid #30363d; }
  .dot { display:inline-block; width:6px; height:6px; border-radius:50%; margin-right:4px; }
  .dot.idle { background:#555; }
  .dot.busy { background:#e94560; animation:pulse 0.6s infinite; }
  .dot.done { background:#4ecca3; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
  ::-webkit-scrollbar { width:3px; }
  ::-webkit-scrollbar-track { background:#16213e; }
  ::-webkit-scrollbar-thumb { background:#ffe66d; border-radius:2px; }
</style>
</head>
<body>
<div class="game-wrap">
  <div class="top-bar">
    <h1>EREZ'in OFISI</h1>
    <span>CodeCrew v1.0</span>
  </div>
  <canvas id="c" width="800" height="600"></canvas>
  <div class="panel">
    <div class="task-row">
      <input type="text" id="t" placeholder="proje gorevi tanimla..." autofocus>
      <button id="b" onclick="baslat()">GONDER</button>
    </div>
    <div class="monitor" id="mon"></div>
    <div id="log"></div>
  </div>
</div>

<script>
const EMOJIS = {"Alp":"🧠","Cem":"💻","Rusty":"👁️","Testo":"🧪","Bug":"🐛","Devina":"🚀","Doc":"📖","Ideator":"💡"};
const ROLS = {"Alp":"Lider","Cem":"Dev","Rusty":"Review","Testo":"Test","Bug":"Hunter","Devina":"DevOps","Doc":"Doc","Ideator":"Idea"};
const PALET = {alp:["#e94560","#4ecdc4","#1a1a2e"], cem:["#2ecc71","#27ae60","#1a1a2e"],
  rusty:["#95a5a6","#7f8c8d","#1a1a2e"], testo:["#9b59b6","#8e44ad","#1a1a2e"],
  bug:["#e74c3c","#c0392b","#1a1a2e"], devina:["#3498db","#2980b9","#1a1a2e"],
  doc:["#ecf0f1","#bdc3c7","#1a1a2e"], ideator:["#f1c40f","#f39c12","#1a1a2e"]};
const KEYS=Object.keys(PALET);

const ROOMS = {
  meeting:{x:9,y:1,w:7,h:4,color:"#4ecdc4",label:"TOPLANTI"},
  cem:{x:1,y:1,w:4,h:3,color:"#2ecc71",label:"CEM"},
  alp:{x:6,y:1,w:3,h:3,color:"#4ecdc4",label:"ALP"},
  devina:{x:17,y:1,w:4,h:3,color:"#3498db",label:"DEVINA"},
  rusty:{x:1,y:5,w:4,h:3,color:"#95a5a6",label:"RUSTY"},
  testo:{x:6,y:5,w:4,h:3,color:"#9b59b6",label:"TESTO"},
  bug:{x:11,y:5,w:4,h:3,color:"#e74c3c",label:"BUG"},
  doc:{x:16,y:5,w:4,h:3,color:"#bdc3c7",label:"DOC"},
  ideator:{x:6,y:9,w:4,h:3,color:"#f1c40f",label:"IDEATOR"},
  erez:{x:1,y:9,w:5,h:4,color:"#ffe66d",label:"EREZ (PATRON)"},
  koridor:{x:11,y:9,w:9,h:4,color:"#1a1a3e",label:""},
};

const AGENT_ROOM = {Alp:"alp",Cem:"cem",Rusty:"rusty",Testo:"testo",
  Bug:"bug",Devina:"devina",Doc:"doc",Ideator:"ideator"};

let agents = {};
["Alp","Cem","Rusty","Testo","Bug","Devina","Doc","Ideator"].forEach((n,i)=>{
  const r = ROOMS[AGENT_ROOM[n]];
  const px = (r.x+1)*32+8, py = (r.y+1)*32+8;
  agents[n] = {
    x:px, y:py, tx:px, ty:py, mx:px, my:py,
    walk:0, walkDir:0, step:0,
    col:PALET[KEYS[i]], emoji:EMOJIS[n],
    say:"", sayT:0, state:"idle"
  };
});

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

// ---- DRAWING ----
function drawTile(x,y,w,h,c){
  ctx.fillStyle=c; ctx.fillRect(x,y,w,h);
  ctx.strokeStyle="rgba(255,255,255,0.05)"; ctx.strokeRect(x,y,w,h);
}

function drawFloor(){
  for(let y=0;y<19;y++) for(let x=0;x<25;x++)
    drawTile(x*32,y*32,32,32,(x+y)%2===0?"#14142e":"#1a1a3e");
}

function drawRoom(r){
  const rx=r.x*32, ry=r.y*32, rw=r.w*32, rh=r.h*32;
  ctx.fillStyle=r.color+"18"; ctx.fillRect(rx,ry,rw,rh);
  ctx.strokeStyle=r.color+"66"; ctx.lineWidth=2; ctx.strokeRect(rx,ry,rw,rh);
  // label
  if(r.label){
    ctx.fillStyle=r.color; ctx.font="bold 10px monospace"; ctx.textAlign="center";
    ctx.fillText(r.label, rx+rw/2, ry+rh-6);
  }
}

function drawDesk(x,y,c){
  ctx.fillStyle=c+"88"; ctx.fillRect(x-14,y-6,28,16);
  ctx.fillStyle=c; ctx.fillRect(x-12,y-4,24,12);
  ctx.strokeStyle="#00000044"; ctx.lineWidth=1; ctx.strokeRect(x-12,y-4,24,12);
  // laptop
  ctx.fillStyle="#222"; ctx.fillRect(x-6,y-6,12,8);
  ctx.fillStyle="#333"; ctx.fillRect(x-5,y-6,10,6);
  ctx.fillStyle="#4ecdc4"; ctx.fillRect(x-3,y-5,6,4);
  // screen glow
  ctx.fillStyle="#4ecdc422"; ctx.fillRect(x-3,y-5,6,4);
}

function drawPlant(x,y){
  ctx.fillStyle="#2d5016"; ctx.fillRect(x-3,y,6,10);
  ctx.fillStyle="#3a7d1a"; ctx.beginPath(); ctx.arc(x,y-2,7,0,Math.PI*2); ctx.fill();
  ctx.fillStyle="#4a9d2a"; ctx.beginPath(); ctx.arc(x-4,y-4,4,0,Math.PI*2); ctx.fill();
  ctx.beginPath(); ctx.arc(x+4,y-4,4,0,Math.PI*2); ctx.fill();
}

function drawClock(x,y){
  ctx.fillStyle="#333"; ctx.beginPath(); ctx.arc(x,y,6,0,Math.PI*2); ctx.fill();
  ctx.fillStyle="#fff"; ctx.beginPath(); ctx.arc(x,y,5,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle="#333"; ctx.lineWidth=1;
  ctx.beginPath(); ctx.moveTo(x,y); ctx.lineTo(x+3,y-3); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x,y); ctx.lineTo(x+2,y+1); ctx.stroke();
}

function drawAgent(n, a){
  const ax=Math.round(a.x), ay=Math.round(a.y);

  // shadow
  ctx.fillStyle="rgba(0,0,0,0.3)"; ctx.beginPath();
  ctx.ellipse(ax, ay+16, 10, 4, 0, 0, Math.PI*2); ctx.fill();

  // body bob
  const bob = a.walk > 0 ? Math.sin(a.step*0.3)*2 : 0;

  // legs
  const legSwing = a.walk > 0 ? Math.sin(a.step*0.3)*4 : 0;
  ctx.fillStyle = a.col[2];
  ctx.fillRect(ax-7, ay+4+bob, 5, 10); // left leg
  ctx.fillRect(ax+2, ay+4+bob, 5, 10); // right leg

  // body
  ctx.fillStyle = a.col[0];
  ctx.beginPath(); ctx.roundRect(ax-10, ay-10+bob, 20, 18, 3); ctx.fill();

  // head
  ctx.fillStyle = a.col[1];
  ctx.beginPath(); ctx.arc(ax, ay-16+bob, 9, 0, Math.PI*2); ctx.fill();

  // eyes
  ctx.fillStyle = "#fff";
  ctx.fillRect(ax-4, ay-19+bob, 4, 4);
  ctx.fillRect(ax+1, ay-19+bob, 4, 4);
  ctx.fillStyle = "#111";
  ctx.fillRect(ax-3, ay-18+bob, 2, 2);
  ctx.fillRect(ax+2, ay-18+bob, 2, 2);

  // mouth
  ctx.fillStyle = "#111";
  ctx.fillRect(ax-2, ay-12+bob, 4, 1);

  // emoji badge
  ctx.font = "9px monospace"; ctx.textAlign = "center";
  ctx.fillText(a.emoji, ax, ay-30+bob);

  // state dot
  const dotC = a.state==="busy"?"#e94560":a.state==="done"?"#4ecca3":"#555";
  ctx.fillStyle=dotC; ctx.beginPath(); ctx.arc(ax+14, ay-18, 3, 0, Math.PI*2); ctx.fill();

  // speech
  if(a.say && a.sayT>0){
    const lines = wrap(a.say,22);
    const lh=13, bw=Math.min(200, Math.max(80, lines.reduce((m,l)=>Math.max(m,ctx.measureText(l).width+16),0)));
    const bh=lines.length*lh+10, bx=Math.max(0,Math.min(800-bw,ax-bw/2)), by=Math.max(4,ay-55-bh);
    ctx.fillStyle="rgba(0,0,0,0.9)"; ctx.beginPath(); ctx.roundRect(bx,by,bw,bh,4); ctx.fill();
    ctx.strokeStyle=a.col[0]; ctx.lineWidth=1; ctx.strokeRect(bx,by,bw,bh);
    ctx.fillStyle="#fff"; ctx.font="10px monospace"; ctx.textAlign="center";
    lines.forEach((l,i)=>ctx.fillText(l,bx+bw/2,by+12+i*lh));
  }
}

function wrap(t,n){
  const w=t.split(' '); const l=[]; let c='';
  w.forEach(w=>{(c+' '+w).length>n? (l.push(c),c=w):c=c?c+' '+w:w;});
  if(c) l.push(c); return l.length?l:[''];
}

function drawOffice(){
  drawFloor();
  Object.values(ROOMS).forEach(drawRoom);

  // manager room special
  const mr=ROOMS.erez;
  ctx.strokeStyle="#ffe66d"; ctx.lineWidth=2; ctx.setLineDash([5,5]);
  ctx.strokeRect(mr.x*32,mr.y*32,mr.w*32,mr.h*32); ctx.setLineDash([]);
  ctx.fillStyle="#ffe66d22"; ctx.fillRect(mr.x*32,mr.y*32,mr.w*32,mr.h*32);
  ctx.fillStyle="#ffe66d"; ctx.font="bold 16px monospace"; ctx.textAlign="center";
  ctx.fillText(">>> EREZ <<<", mr.x*32+mr.w*16, mr.y*32+24);
  ctx.font="11px monospace"; ctx.fillStyle="#ffe66d88";
  ctx.fillText("PATRON / YONETICI", mr.x*32+mr.w*16, mr.y*32+40);
  ctx.font="10px monospace"; ctx.fillText("--- makam ---", mr.x*32+mr.w*16, mr.y*32+mr.h*32-8);

  // desks in rooms
  Object.entries(ROOMS).forEach(([k,r])=>{
    if(k==="koridor"||k==="meeting"||k==="erez") return;
    drawDesk(r.x*32+r.w*8, r.y*32+r.h*12+8, r.color);
  });

  // meeting table
  const mt=ROOMS.meeting;
  ctx.fillStyle="#4ecdc444"; ctx.beginPath();
  ctx.roundRect(mt.x*32+mt.w*8-24, mt.y*32+mt.h*8-10, 48, 20, 4); ctx.fill();
  ctx.strokeStyle="#4ecdc4"; ctx.strokeRect(mt.x*32+mt.w*8-24, mt.y*32+mt.h*8-10, 48, 20);

  // meeting chairs
  for(let i=0;i<4;i++){
    const cx=mt.x*32+mt.w*8-12+i*8, cy=mt.y*32+mt.h*8+18;
    ctx.fillStyle="#333"; ctx.beginPath(); ctx.roundRect(cx-5,cy,10,8,2); ctx.fill();
  }

  // Erez's desk (special - bigger)
  const ex=mr.x*32+mr.w*8, ey=mr.y*32+60;
  ctx.fillStyle="#ffe66d44"; ctx.fillRect(ex-22,ey-8,44,20);
  ctx.fillStyle="#ffe66d"; ctx.fillRect(ex-20,ey-6,40,16);
  ctx.fillStyle="#222"; ctx.fillRect(ex-10,ey-8,20,12);
  ctx.fillStyle="#4ecdc4"; ctx.fillRect(ex-8,ey-7,16,8);
  // laptop glow
  ctx.fillStyle="#4ecdc444"; ctx.fillRect(ex-8,ey-7,16,8);

  // decor
  drawPlant(ROOMS.cem.x*32+ROOMS.cem.w*32-20, ROOMS.cem.y*32+ROOMS.cem.h*32-20);
  drawPlant(ROOMS.devina.x*32+ROOMS.devina.w*32-20, ROOMS.devina.y*32+ROOMS.devina.h*32-20);
  drawPlant(ROOMS.erez.x*32+ROOMS.erez.w*32-20, ROOMS.erez.y*32+ROOMS.erez.h*32-20);

  drawClock(ROOMS.koridor.x*32+ROOMS.koridor.w*8, ROOMS.koridor.y*32+12);
}

// ---- AGENT MOVEMENT ----
function moveTo(name,tx,ty){
  const a=agents[name]; if(!a)return;
  a.tx=tx; a.ty=ty; a.walk=1;
}

function moveToRoom(name,key){
  const r=ROOMS[key]; if(!r)return;
  moveTo(name, r.x*32+r.w*8, r.y*32+r.h*12);
}

function updateMovement(){
  Object.values(agents).forEach(a=>{
    if(!a.walk) return;
    const dx=a.tx-a.x, dy=a.ty-a.y, d=Math.sqrt(dx*dx+dy*dy);
    if(d<1.5){ a.x=a.tx; a.y=a.ty; a.walk=0; a.step=0; return; }
    if(dx>0) a.walkDir=1; else if(dx<0) a.walkDir=-1;
    a.x+=dx*0.08; a.y+=dy*0.08;
    a.step+=0.5;
  });
}

function say(name,text){
  const a=agents[name]; if(!a)return;
  a.say=text; a.sayT=180; a.state="busy";
}

function stopSay(name){
  const a=agents[name]; if(a) a.say="";
}

// ---- GAME LOOP ----
function loop(){
  updateMovement();
  ctx.clearRect(0,0,800,600);
  drawOffice();
  Object.entries(agents).forEach(([n,a])=>{
    if(a.sayT>0) a.sayT--;
    drawAgent(n,a);
  });
  requestAnimationFrame(loop);
}

// polyfill
if(!CanvasRenderingContext2D.prototype.roundRect){
  CanvasRenderingContext2D.prototype.roundRect=function(x,y,w,h,r){
    this.moveTo(x+r,y); this.arcTo(x+w,y,x+w,y+h,r);
    this.arcTo(x+w,y+h,x,y+h,r); this.arcTo(x,y+h,x,y,r);
    this.arcTo(x,y,x+w,y,r);
  };
}

// ---- SSE ----
function baslat(){
  const input=document.getElementById('t'), task=input.value.trim();
  if(!task)return;
  const btn=document.getElementById('b'); btn.disabled=true;

  const log=document.getElementById('log'); log.innerHTML=''; log.style.display='block';

  // agents to meeting
  Object.keys(agents).forEach(n=>{
    moveToRoom(n,"meeting");
    agents[n].state="idle"; agents[n].say="";
  });
  updateMon();

  const es=new EventSource('/stream?task='+encodeURIComponent(task));
  es.onmessage=function(e){
    const d=JSON.parse(e.data);
    if(d.type==='message'){
      const a=agents[d.name];
      if(a){
        moveToRoom(d.name,"meeting");
        say(d.name, d.message.substring(0,120));
        updateMon();

        const r=document.createElement('div'); r.className='log-msg';
        r.innerHTML='<b>'+d.emoji+' '+d.name+':</b> '+esc(d.message.substring(0,150));
        log.appendChild(r); log.scrollTop=log.scrollHeight;
      }
    } else if(d.type==='summary'){
      Object.values(agents).forEach(a=>{a.state="done"; a.sayT=0;});
      updateMon();
      const r=document.createElement('div'); r.className='log-msg';
      r.style.color='#4ecca3'; r.textContent='✓ Proje tamamlandi!';
      log.appendChild(r);
      // move agents back to rooms
      Object.keys(agents).forEach(n=>moveToRoom(n,AGENT_ROOM[n]));
    } else if(d.type==='done'){ btn.disabled=false; es.close(); }
    else if(d.type==='error'){ btn.disabled=false; es.close(); }
  };
  es.onerror=function(){ btn.disabled=false; es.close(); };
}

function updateMon(){
  const m=document.getElementById('mon');
  m.innerHTML=Object.entries(agents).map(([n,a])=>{
    const cls=a.state==="busy"?"busy":a.state==="done"?"done":"idle";
    return `<span><span class="dot ${cls}"></span>${a.emoji} ${n}</span>`;
  }).join('');
}

function esc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

document.getElementById('t').addEventListener('keydown',e=>{if(e.key==='Enter')baslat();});

loop();
updateMon();
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


@app.get("/stream")
async def stream(task: str):
    async def event_generator():
        orchestrator = Orchestrator()

        def collect():
            messages = []
            def handler(msg):
                messages.append({
                    "type": "message",
                    "name": msg.agent_name,
                    "emoji": msg.emoji,
                    "role": msg.role,
                    "message": msg.message,
                })
            summary_text = orchestrator.run(task, on_message=handler)
            for msg in messages:
                yield {"event": "message", "data": json.dumps(msg, ensure_ascii=False)}
            yield {"event": "message", "data": json.dumps({
                "type": "summary", "content": summary_text,
            }, ensure_ascii=False)}
            yield {"event": "message", "data": json.dumps({"type": "done"})}

        return EventSourceResponse(collect())

    gen = await event_generator()
    return gen


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
