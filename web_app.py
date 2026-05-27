import json
from fastapi import FastAPI
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
<title>CodeCrew - 3D Office</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#000;overflow:hidden;font-family:'Segoe UI',sans-serif}
  canvas{display:block}
  #ui{position:absolute;bottom:20px;left:50%;transform:translateX(-50%);
      width:90%;max-width:700px;z-index:10}
  .panel{background:rgba(15,15,30,0.92);border:1px solid rgba(255,255,255,0.1);
         border-radius:12px;padding:14px 18px;backdrop-filter:blur(10px)}
  .row{display:flex;gap:10px}
  .row input{flex:1;padding:10px 14px;border-radius:8px;border:1px solid rgba(255,255,255,0.15);
             background:rgba(0,0,0,0.4);color:#fff;font-size:15px;outline:none}
  .row input:focus{border-color:#ffe66d}
  .row input::placeholder{color:#666}
  .row button{padding:10px 24px;border-radius:8px;border:none;background:#ffe66d;
              color:#000;font-size:15px;font-weight:700;cursor:pointer}
  .row button:hover{background:#fff3a0}
  .row button:disabled{opacity:0.4;cursor:default}
  #info{position:absolute;top:16px;left:50%;transform:translateX(-50%);
        z-index:10;text-align:center;pointer-events:none}
  #info h1{font-size:20px;color:#ffe66d;text-shadow:0 0 20px rgba(255,230,109,0.3);
           letter-spacing:2px}
  #info p{font-size:12px;color:#888;margin-top:4px}
  #log{position:absolute;top:70px;right:16px;z-index:10;width:280px;max-height:400px;
       overflow-y:auto;pointer-events:none}
  .msg{padding:6px 10px;margin-bottom:4px;border-radius:6px;
       background:rgba(15,15,30,0.8);border-left:3px solid #ffe66d;
       font-size:12px;color:#ccc;line-height:1.4;opacity:0;transform:translateX(20px);
       animation:fadeIn 0.4s forwards}
  .msg b{color:#fff}
  @keyframes fadeIn{to{opacity:1;transform:translateX(0)}}
  #hud{position:absolute;bottom:90px;left:50%;transform:translateX(-50%);
       z-index:10;display:flex;gap:8px;flex-wrap:wrap;justify-content:center}
  .tag{padding:4px 10px;border-radius:20px;background:rgba(15,15,30,0.8);
       border:1px solid rgba(255,255,255,0.1);font-size:11px;color:#aaa;
       display:flex;align-items:center;gap:4px}
  .tag .dot{width:6px;height:6px;border-radius:50%}
  .tag .idle{background:#555}
  .tag .busy{background:#e94560;animation:pulse 0.6s infinite}
  .tag .done{background:#4ecca3}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.3}}
  ::-webkit-scrollbar{width:3px}
  ::-webkit-scrollbar-track{background:transparent}
  ::-webkit-scrollbar-thumb{background:#ffe66d44;border-radius:2px}
</style>
</head>
<body>
<div id="info"><h1>✦ EREZ'in OFISI ✦</h1><p>fare ile surukle • zoom yap • 360° dolas</p></div>
<div id="hud"></div>
<div id="log"></div>
<div id="ui">
<div class="panel">
<div class="row">
<input type="text" id="t" placeholder="proje gorevini yaz..." autofocus>
<button id="btn" onclick="baslat()">GONDER</button>
</div></div></div>

<script type="importmap">
{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
"three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}
</script>
<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';

const AGENT_DATA = """ + json.dumps([
    {"name": a["name"], "emoji": a["emoji"], "role": a["role"]}
    for a in AGENTS
], ensure_ascii=False) + """;

const COLORS = {
  Alp:0x4ecdc4, Cem:0x2ecc71, Rusty:0x95a5a6, Testo:0x9b59b6,
  Bug:0xe74c3c, Devina:0x3498db, Doc:0xecf0f1, Ideator:0xf1c40f
};

const ROOMS = {
  Alp:{pos:[-4,0,7]}, Cem:{pos:[-8,0,7]}, Devina:{pos:[4,0,7]},
  Rusty:{pos:[-8,0,-7]}, Testo:{pos:[-4,0,-7]}, Bug:{pos:[0,0,-7]},
  Doc:{pos:[4,0,-7]}, Ideator:{pos:[8,0,7]},
  Meeting:{pos:[0,0,0]}, Erez:{pos:[7,0,-7]}
};

// --- SCENE ---
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0a0a1a);
scene.fog = new THREE.Fog(0x0a0a1a, 25, 40);

const camera = new THREE.PerspectiveCamera(45, window.innerWidth/window.innerHeight, 0.1, 50);
camera.position.set(14, 16, 14);
camera.lookAt(0, 0, 0);

const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.2;
document.body.prepend(renderer.domElement);

const labelRenderer = new CSS2DRenderer();
labelRenderer.setSize(window.innerWidth, window.innerHeight);
labelRenderer.domElement.style.position = 'absolute';
labelRenderer.domElement.style.top = '0';
labelRenderer.domElement.style.pointerEvents = 'none';
document.body.prepend(labelRenderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 5;
controls.maxDistance = 30;
controls.maxPolarAngle = Math.PI / 2.1;
controls.target.set(0, 1, 0);

// --- LIGHTS ---
const ambient = new THREE.AmbientLight(0x404060, 0.4);
scene.add(ambient);

const hemi = new THREE.HemisphereLight(0x4ecdc4, 0x1a1a2e, 0.6);
scene.add(hemi);

const dir = new THREE.DirectionalLight(0xffeedd, 2);
dir.position.set(10, 20, 5);
dir.castShadow = true;
dir.shadow.mapSize.width = 1024;
dir.shadow.mapSize.height = 1024;
dir.shadow.camera.near = 0.5;
dir.shadow.camera.far = 30;
dir.shadow.camera.left = -15;
dir.shadow.camera.right = 15;
dir.shadow.camera.top = 15;
dir.shadow.camera.bottom = -15;
scene.add(dir);

const fill = new THREE.DirectionalLight(0x4ecdc4, 0.3);
fill.position.set(-5, 10, -10);
scene.add(fill);

// --- FLOOR ---
const floor = new THREE.Mesh(
  new THREE.PlaneGeometry(26, 26),
  new THREE.MeshStandardMaterial({color:0x1a1a2e, roughness:0.8, metalness:0.1})
);
floor.rotation.x = -Math.PI/2;
floor.receiveShadow = true;
scene.add(floor);

// grid
const grid = new THREE.GridHelper(26, 26, 0x4ecdc4, 0x303060);
grid.position.y = 0.01;
scene.add(grid);

// --- BUILDING MATERIALS ---
const wallMat = new THREE.MeshStandardMaterial({color:0x2a2a4a, roughness:0.6, metalness:0.1, transparent:true, opacity:0.3});
const wallFrame = new THREE.MeshStandardMaterial({color:0x4a4a6a, roughness:0.5, metalness:0.2});
const deskMat = new THREE.MeshStandardMaterial({color:0x5a4030, roughness:0.7});
const deskTop = new THREE.MeshStandardMaterial({color:0x6a5040, roughness:0.6});
const screenMat = new THREE.MeshStandardMaterial({color:0x1a1a2e, emissive:0x4ecdc4, emissiveIntensity:0.15});
const chairMat = new THREE.MeshStandardMaterial({color:0x333355, roughness:0.5});
const plantMat = new THREE.MeshStandardMaterial({color:0x2a5a1a});
const potMat = new THREE.MeshStandardMaterial({color:0x6a4a3a});

// --- FURNITURE FACTORY ---
function makeDesk(x,z, rot=0, color=0x5a4030){
  const g = new THREE.Group();
  const m = new THREE.MeshStandardMaterial({color, roughness:0.7});
  // legs
  [[-1.2,-0.6],[1.2,-0.6],[-1.2,0.6],[1.2,0.6]].forEach(([lx,lz])=>{
    const leg = new THREE.Mesh(new THREE.BoxGeometry(0.15,0.7,0.15), m);
    leg.position.set(lx,0.35,lz); leg.castShadow=true; g.add(leg);
  });
  const top = new THREE.Mesh(new THREE.BoxGeometry(2.8,0.08,1.4), new THREE.MeshStandardMaterial({color:color+0x111111, roughness:0.5}));
  top.position.y=0.75; top.castShadow=true; top.receiveShadow=true; g.add(top);
  g.position.set(x,0,z); g.rotation.y=rot; return g;
}

function makeMonitor(x,y,z, rot=0){
  const g = new THREE.Group();
  const base = new THREE.Mesh(new THREE.BoxGeometry(0.6,0.05,0.5), new THREE.MeshStandardMaterial({color:0x222233}));
  base.position.y=0.025; g.add(base);
  const stand = new THREE.Mesh(new THREE.BoxGeometry(0.08,0.4,0.08), new THREE.MeshStandardMaterial({color:0x333344}));
  stand.position.y=0.25; g.add(stand);
  const screen = new THREE.Mesh(new THREE.BoxGeometry(0.8,0.55,0.04), screenMat);
  screen.position.y=0.5; g.add(screen);
  // glow
  const glow = new THREE.Mesh(new THREE.BoxGeometry(0.72,0.47,0.01), new THREE.MeshStandardMaterial({
    color:0x4ecdc4, emissive:0x4ecdc4, emissiveIntensity:0.3, transparent:true, opacity:0.6
  }));
  glow.position.set(0,0.5,-0.03); g.add(glow);
  g.position.set(x,y+0.75,z); g.rotation.y=rot; return g;
}

function makeChair(x,z, rot=0, color=0x333355){
  const g = new THREE.Group();
  const m = new THREE.MeshStandardMaterial({color, roughness:0.5});
  const base = new THREE.Mesh(new THREE.CylinderGeometry(0.5,0.6,0.08,8), m);
  base.position.y=0.04; base.receiveShadow=true; g.add(base);
  const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.04,0.04,0.5,6), new THREE.MeshStandardMaterial({color:0x444466}));
  pole.position.y=0.3; g.add(pole);
  const seat = new THREE.Mesh(new THREE.BoxGeometry(0.7,0.06,0.7), new THREE.MeshStandardMaterial({color:color+0x222222, roughness:0.7}));
  seat.position.y=0.55; seat.castShadow=true; g.add(seat);
  const back = new THREE.Mesh(new THREE.BoxGeometry(0.7,0.6,0.06), m);
  back.position.set(0,0.85,-0.35); back.castShadow=true; g.add(back);
  g.position.set(x,0,z); g.rotation.y=rot; return g;
}

function makePlant(x,z){
  const g = new THREE.Group();
  const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.4,0.35,0.4,6), potMat);
  pot.position.y=0.2; g.add(pot);
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.03,0.05,0.6,4), new THREE.MeshStandardMaterial({color:0x3a6a2a}));
  stem.position.y=0.6; g.add(stem);
  for(let i=0;i<8;i++){
    const a=i*Math.PI/4;
    const leaf = new THREE.Mesh(new THREE.ConeGeometry(0.2,0.35,4), new THREE.MeshStandardMaterial({color:0x3a8a2a}));
    leaf.position.set(Math.cos(a)*0.15,0.85+Math.sin(i)*0.1,Math.sin(a)*0.15);
    leaf.rotation.x=Math.cos(a)*0.4; leaf.rotation.z=Math.sin(a)*0.4;
    g.add(leaf);
  }
  g.position.set(x,0,z); return g;
}

function makeRoomLabel(text, x, z, color='#4ecdc4'){
  const d=document.createElement('div');
  d.textContent=text; d.style.color=color; d.style.fontFamily='monospace';
  d.style.fontSize='12px'; d.style.fontWeight='bold';
  d.style.textShadow='0 0 10px rgba(0,0,0,0.8)';
  d.style.background='rgba(0,0,0,0.5)'; d.style.padding='2px 8px';
  d.style.borderRadius='4px'; d.style.border='1px solid '+color+'44';
  const l=new CSS2DObject(d); l.position.set(x,2.8,z); return l;
}

// --- BUILD OFFICE ---
// Room platforms
Object.values(ROOMS).forEach(r => {
  const plat = new THREE.Mesh(
    new THREE.PlaneGeometry(3.5, 3.5),
    new THREE.MeshStandardMaterial({color:0x222244, roughness:0.7, transparent:true, opacity:0.5})
  );
  plat.rotation.x=-Math.PI/2;
  plat.position.set(r.pos[0],0.02,r.pos[2]);
  plat.receiveShadow=true;
  scene.add(plat);
});

// Add furniture to each room
Object.entries(ROOMS).forEach(([name, r]) => {
  const [x, y, z] = r.pos;
  if(name==='Meeting'){
    // big table
    const mt = new THREE.Mesh(new THREE.BoxGeometry(4,0.1,1.5), new THREE.MeshStandardMaterial({color:0x3a4a5a, roughness:0.5}));
    mt.position.set(x,0.75,z); mt.castShadow=true; mt.receiveShadow=true; scene.add(mt);
    [[-1.5,0],[1.5,0],[-1.5,-0.5],[1.5,-0.5]].forEach(([mx,mz])=>{
      const ml = new THREE.Mesh(new THREE.CylinderGeometry(0.06,0.06,0.7,6), new THREE.MeshStandardMaterial({color:0x444466}));
      ml.position.set(x+mx,0.35,z+mz); scene.add(ml);
    });
    // chairs around
    [[2,0,0],[0,2,Math.PI/2],[-2,0,Math.PI],[0,-2,-Math.PI/2]].forEach(([cx,cz,cr])=>{
      scene.add(makeChair(x+cx*0.7,z+cz*0.7, cr, 0x333355));
    });
    const label = makeRoomLabel('TOPLANTI', x, z, '#4ecdc4');
    scene.add(label);
  } else if(name==='Erez'){
    // manager special desk
    scene.add(makeDesk(x, z, 0, 0xffe66d));
    scene.add(makeMonitor(x-0.6, 0, z-0.2));
    scene.add(makeChair(x+0.6, z-0.2, Math.PI, 0x333355));
    scene.add(makePlant(x-1.2, z+0.8));
    const label = makeRoomLabel('EREZ (Patron)', x, z, '#ffe66d');
    scene.add(label);
  } else {
    const c = COLORS[name] || 0x888888;
    const cStr = '#'+c.toString(16).padStart(6,'0');
    scene.add(makeDesk(x, z, 0, c));
    scene.add(makeMonitor(x-0.6, 0, z-0.2));
    scene.add(makeChair(x+0.6, z-0.2, Math.PI, 0x333355));
    scene.add(makePlant(x-1.2, z+0.8));
    const label = makeRoomLabel(name, x, z, cStr);
    scene.add(label);
  }
});

// --- AGENTS ---
let meshes = {};
AGENT_DATA.forEach(d => {
  const g = new THREE.Group();
  const c = COLORS[d.name] || 0x888888;

  // body
  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.4,0.5,0.8,8),
    new THREE.MeshStandardMaterial({color:c, roughness:0.6}));
  body.position.y=0.7; body.castShadow=true; g.add(body);

  // head
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.3,8,6),
    new THREE.MeshStandardMaterial({color:0xf4c2c2, roughness:0.5}));
  head.position.y=1.2; head.castShadow=true; g.add(head);

  // eyes
  const eMat = new THREE.MeshStandardMaterial({color:0x222222});
  [-0.1,0.1].forEach(ex=>{
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.06,6,6), eMat);
    eye.position.set(ex,1.25,0.28); g.add(eye);
  });

  // label above
  const lbl = document.createElement('div');
  lbl.textContent = d.emoji + ' ' + d.name;
  lbl.style.color = '#fff';
  lbl.style.fontSize = '11px';
  lbl.style.fontWeight = 'bold';
  lbl.style.textShadow = '0 0 8px rgba(0,0,0,0.9)';
  lbl.style.background = 'rgba(0,0,0,0.6)';
  lbl.style.padding = '2px 8px';
  lbl.style.borderRadius = '12px';
  lbl.style.border = '1px solid #' + c.toString(16).padStart(6,'0');
  lbl.style.whiteSpace = 'nowrap';
  const label = new CSS2DObject(lbl);
  label.position.y = 1.7;
  g.add(label);

  // place at their room
  const room = ROOMS[d.name];
  if(room){
    g.position.set(room.pos[0], 0, room.pos[2]);
  }

  scene.add(g);
  meshes[d.name] = g;
});

// --- ANIMATION ---
window.addEventListener('resize', ()=>{
  camera.aspect = window.innerWidth/window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  labelRenderer.setSize(window.innerWidth, window.innerHeight);
});

let time = 0;
function animate(){
  requestAnimationFrame(animate);
  time += 0.02;
  controls.update();

  // subtle agent bob
  Object.values(meshes).forEach((m,i)=>{
    m.position.y = Math.sin(time + i*0.8) * 0.02;
    m.rotation.y += 0.002;
  });

  renderer.render(scene, camera);
  labelRenderer.render(scene, camera);
}
animate();

// --- SSE INTEGRATION ---
let agentStates = {};
AGENT_DATA.forEach(d => agentStates[d.name] = 'idle');

function updateHUD(){
  const h = document.getElementById('hud');
  h.innerHTML = AGENT_DATA.map(d => {
    const s = agentStates[d.name] || 'idle';
    return `<span class="tag"><span class="dot ${s}"></span>${d.emoji} ${d.name}</span>`;
  }).join('');
}
updateHUD();

function moveTo(name, tx, tz){
  const m = meshes[name];
  if(m){
    m.position.x = tx;
    m.position.z = tz;
  }
}

function moveToRoom(name, rname){
  const room = ROOMS[rname];
  if(room) moveTo(name, room.pos[0], room.pos[2]);
}

function sayAgent(name, text){
  agentStates[name] = 'busy';
  updateHUD();
  moveToRoom(name, 'Meeting');
  const m = meshes[name];
  if(m){
    // add floating speech
    const existing = m.userData.speech;
    if(existing){ m.remove(existing); }

    const d = document.createElement('div');
    d.textContent = text.substring(0,60);
    d.style.color = '#fff';
    d.style.fontSize = '10px';
    d.style.background = 'rgba(0,0,0,0.85)';
    d.style.padding = '4px 10px';
    d.style.borderRadius = '8px';
    d.style.border = '1px solid #ffe66d44';
    d.style.maxWidth = '160px';
    d.style.whiteSpace = 'normal';
    d.style.wordWrap = 'break-word';
    d.style.fontFamily = 'monospace';
    d.style.lineHeight = '1.3';
    const lbl = new CSS2DObject(d);
    lbl.position.y = 2.5;
    m.add(lbl);
    m.userData.speech = lbl;
  }
}

function clearSpeech(name){
  const m = meshes[name];
  if(m && m.userData.speech){
    m.remove(m.userData.speech);
    m.userData.speech = null;
  }
}

function resetAgents(){
  AGENT_DATA.forEach(d => {
    agentStates[d.name] = 'idle';
    clearSpeech(d.name);
    const room = ROOMS[d.name];
    if(room) moveTo(d.name, room.pos[0], room.pos[2]);
  });
  updateHUD();
}

function doneAgents(){
  AGENT_DATA.forEach(d => {
    agentStates[d.name] = 'done';
    clearSpeech(d.name);
    const room = ROOMS[d.name];
    if(room) moveTo(d.name, room.pos[0], room.pos[2]);
  });
  updateHUD();
}

// --- START ---
function baslat(){
  const inp = document.getElementById('t');
  const task = inp.value.trim();
  if(!task) return;
  const btn = document.getElementById('btn');
  btn.disabled = true;
  resetAgents();

  const log = document.getElementById('log');
  log.innerHTML = '';

  const es = new EventSource('/stream?task=' + encodeURIComponent(task));
  es.onmessage = function(e){
    const data = JSON.parse(e.data);
    if(data.type === 'message'){
      sayAgent(data.name, data.message);
      const row = document.createElement('div');
      row.className = 'msg';
      row.innerHTML = '<b>'+data.emoji+' '+data.name+':</b> '+esc(data.message.substring(0,150));
      log.appendChild(row);
      log.scrollTop = log.scrollHeight;
    } else if(data.type === 'summary'){
      doneAgents();
      const row = document.createElement('div');
      row.className = 'msg';
      row.style.borderLeftColor = '#4ecca3';
      row.innerHTML = '<b>✓ Proje tamamlandi</b>';
      log.appendChild(row);
    } else if(data.type === 'done'){
      btn.disabled = false;
      es.close();
    } else if(data.type === 'error'){
      btn.disabled = false;
      es.close();
    }
  };
  es.onerror = function(){
    btn.disabled = false;
    es.close();
  };
}

function esc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

document.getElementById('t').addEventListener('keydown',e=>{if(e.key==='Enter')baslat();});
window.baslat = baslat;
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
