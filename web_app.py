import asyncio
import json
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
from masa.core import Orchestrator
from masa.agents import AGENTS

app = FastAPI(title="CodeCrew")

HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CodeCrew - Pixel Office</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background: #1a1a2e; color: #e0e0e0; font-family: 'Courier New', monospace;
         display: flex; justify-content: center; padding: 10px; overflow-x: hidden; }
  .game-container { max-width: 820px; width: 100%; }
  canvas { display: block; margin: 0 auto; border: 2px solid #30363d;
           border-radius: 4px; image-rendering: pixelated; width: 100%;
           max-width: 800px; background: #16213e; }
  .ui-panel { background: #0f3460; border: 2px solid #30363d; border-top: none;
              padding: 12px; border-radius: 0 0 8px 8px; }
  .task-row { display: flex; gap: 8px; }
  .task-row input { flex: 1; padding: 10px 14px; border-radius: 6px;
                    border: 1px solid #30363d; background: #16213e;
                    color: #e0e0e0; font-size: 14px; font-family: inherit; }
  .task-row input:focus { outline: none; border-color: #e94560; }
  .task-row button { padding: 10px 20px; border-radius: 6px; border: none;
                     background: #e94560; color: #fff; font-size: 14px;
                     cursor: pointer; font-weight: bold; font-family: inherit; }
  .task-row button:hover { background: #ff6b6b; }
  .task-row button:disabled { opacity: 0.4; cursor: not-allowed; }
  #log { margin-top: 12px; max-height: 200px; overflow-y: auto;
         padding: 8px; background: #16213e; border-radius: 4px;
         font-size: 13px; line-height: 1.5; display: none; }
  .log-msg { padding: 4px 0; border-bottom: 1px solid #1a1a2e; }
  .log-msg:last-child { border: none; }
  .status-bar { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px;
                font-size: 12px; color: #8892b0; }
  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%;
         margin-right: 4px; }
  .dot.idle { background: #555; }
  .dot.working { background: #e94560; animation: blink 0.8s infinite; }
  .dot.done { background: #4ecca3; }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
  @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-3px)} }
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: #16213e; }
  ::-webkit-scrollbar-thumb { background: #e94560; border-radius: 2px; }
</style>
</head>
<body>
<div class="game-container">
  <h2 style="text-align:center; margin:10px 0; font-size:20px; color:#e94560;">
    [ CODECREW ]</h2>
  <canvas id="office" width="800" height="600"></canvas>
  <div class="ui-panel">
    <div class="task-row">
      <input type="text" id="taskInput" placeholder="görev tanimla..."
             autocomplete="off" autofocus>
      <button id="runBtn" onclick="startTask()">BASLA</button>
    </div>
    <div class="status-bar" id="statusBar"></div>
    <div id="log"></div>
  </div>
</div>

<script>
const AGENTS = """ + json.dumps([
    {"name": a["name"], "emoji": a["emoji"], "role": a["role"]}
    for a in AGENTS
], ensure_ascii=False) + """;

const COLORS = {
  alp: ["#e94560","#4ecdc4","#1a1a2e","#ffe66d"],
  cem: ["#2ecc71","#27ae60","#1a1a2e","#ffe66d"],
  rusty: ["#95a5a6","#7f8c8d","#1a1a2e","#ffe66d"],
  testo: ["#9b59b6","#8e44ad","#1a1a2e","#ffe66d"],
  bug: ["#e74c3c","#c0392b","#1a1a2e","#ffe66d"],
  devina: ["#3498db","#2980b9","#1a1a2e","#ffe66d"],
  doc: ["#ecf0f1","#bdc3c7","#1a1a2e","#ffe66d"],
  ideator: ["#f1c40f","#f39c12","#1a1a2e","#ffe66d"],
};

const AGENT_COLORS = {};
AGENTS.forEach((a,i) => {
  const keys = Object.keys(COLORS);
  AGENT_COLORS[a.name] = COLORS[keys[i]];
});

const canvas = document.getElementById('office');
const ctx = canvas.getContext('2d');
const T = 32; // tile size

const ROOMS = {
  alp:    {label:"Alp (Lider)", x:10, y:1, w:4, h:3, color:"#4ecdc4"},
  cem:    {label:"Cem (Dev)", x:1, y:1, w:4, h:3, color:"#2ecc71"},
  rusty:  {label:"Rusty (Review)", x:1, y:5, w:4, h:3, color:"#7f8c8d"},
  testo:  {label:"Testo (Test)", x:6, y:5, w:4, h:3, color:"#8e44ad"},
  bug:    {label:"Bug (Hunter)", x:11, y:5, w:4, h:3, color:"#c0392b"},
  devina: {label:"Devina (DevOps)", x:16, y:1, w:4, h:3, color:"#2980b9"},
  doc:    {label:"Doc (Doc)", x:16, y:5, w:4, h:3, color:"#bdc3c7"},
  ideator:{label:"Ideator (Idea)", x:6, y:1, w:4, h:3, color:"#f39c12"},
  meeting:{label:"Toplanti", x:11, y:1, w:4, h:3, color:"#e94560"},
  manager:{label:"Yonetici (Sen)", x:1, y:9, w:6, h:3, color:"#ffe66d"},
};

const AGENT_ROOMS = {
  "Alp": "alp", "Cem": "cem", "Rusty": "rusty", "Testo": "testo",
  "Bug": "bug", "Devina": "devina", "Doc": "doc", "Ideator": "ideator"
};

let agents = {};
AGENTS.forEach(a => {
  agents[a.name] = {
    x: ROOMS[AGENT_ROOMS[a.name]].x * T + T,
    y: ROOMS[AGENT_ROOMS[a.name]].y * T + T,
    targetX: ROOMS[AGENT_ROOMS[a.name]].x * T + T,
    targetY: ROOMS[AGENT_ROOMS[a.name]].y * T + T,
    color: AGENT_COLORS[a.name],
    emoji: a.emoji,
    saying: "",
    sayingTimer: 0,
    state: "idle",
  };
});

function drawOffice() {
  ctx.fillStyle = "#0f3460";
  ctx.fillRect(0, 0, 800, 600);

  // floor tiles
  for (let y = 0; y < 19; y++) {
    for (let x = 0; x < 25; x++) {
      ctx.fillStyle = (x+y) % 2 === 0 ? "#1a1a3e" : "#16213e";
      ctx.fillRect(x*T, y*T, T, T);
    }
  }

  // draw rooms
  Object.values(ROOMS).forEach(r => {
    if (r.label === "Yonetici (Sen)") return;
    const rx = r.x * T, ry = r.y * T, rw = r.w * T, rh = r.h * T;
    ctx.fillStyle = r.color + "22";
    ctx.fillRect(rx, ry, rw, rh);
    ctx.strokeStyle = r.color + "88";
    ctx.lineWidth = 2;
    ctx.strokeRect(rx, ry, rw, rh);
    // label
    ctx.fillStyle = r.color;
    ctx.font = "10px monospace";
    ctx.textAlign = "center";
    ctx.fillText(r.label, rx + rw/2, ry + rh - 6);
  });

  // manager room special
  const mr = ROOMS.manager;
  const mrx = mr.x * T, mry = mr.y * T, mrw = mr.w * T, mrh = mr.h * T;
  ctx.fillStyle = "#ffe66d22";
  ctx.fillRect(mrx, mry, mrw, mrh);
  ctx.strokeStyle = "#ffe66d";
  ctx.lineWidth = 2;
  ctx.setLineDash([4,4]);
  ctx.strokeRect(mrx, mry, mrw, mrh);
  ctx.setLineDash([]);
  ctx.fillStyle = "#ffe66d";
  ctx.font = "bold 14px monospace";
  ctx.textAlign = "center";
  ctx.fillText("YONETICI (SEN)", mrx + mrw/2, mry + 20);
  ctx.font = "10px monospace";
  ctx.fillText("gorev ver", mrx + mrw/2, mry + mrh - 10);

  // hallway labels
  ctx.fillStyle = "#4ecdc4";
  ctx.font = "9px monospace";
  ctx.textAlign = "center";
  ctx.fillText("--- KORIDOR ---", 12*T, 17*T);
}

function drawAgent(name, agent) {
  const ax = Math.floor(agent.x);
  const ay = Math.floor(agent.y);

  // body
  ctx.fillStyle = agent.color[0];
  ctx.beginPath();
  ctx.roundRect(ax-10, ay-8, 20, 22, 4);
  ctx.fill();

  // head
  ctx.fillStyle = agent.color[1];
  ctx.beginPath();
  ctx.arc(ax, ay-14, 8, 0, Math.PI*2);
  ctx.fill();

  // eyes
  ctx.fillStyle = "#fff";
  ctx.fillRect(ax-4, ay-16, 3, 3);
  ctx.fillRect(ax+2, ay-16, 3, 3);
  ctx.fillStyle = "#1a1a2e";
  ctx.fillRect(ax-3, ay-15, 2, 2);
  ctx.fillRect(ax+3, ay-15, 2, 2);

  // emoji badge
  ctx.font = "10px monospace";
  ctx.textAlign = "center";
  ctx.fillText(agent.emoji, ax, ay-24);

  // speech bubble
  if (agent.saying && agent.sayingTimer > 0) {
    const lines = wordWrap(agent.saying, 20);
    const lineH = 14;
    const bw = Math.min(180, lines.reduce((m,l) => Math.max(m, ctx.measureText(l).width + 16), 100));
    const bh = lines.length * lineH + 10;
    const bx = Math.max(2, Math.min(800-bw-2, ax - bw/2));
    const by = ay - 48 - bh;

    ctx.fillStyle = "rgba(0,0,0,0.85)";
    ctx.beginPath();
    ctx.roundRect(bx, by, bw, bh, 4);
    ctx.fill();
    ctx.strokeStyle = agent.color[0];
    ctx.lineWidth = 1;
    ctx.strokeRect(bx, by, bw, bh);

    ctx.fillStyle = "#fff";
    ctx.font = "11px monospace";
    lines.forEach((line, i) => {
      ctx.textAlign = "center";
      ctx.fillText(line, bx + bw/2, by + 12 + i*lineH);
    });
  }

  // state indicator
  if (agent.state === "working") {
    ctx.fillStyle = "#e94560";
    ctx.beginPath();
    ctx.arc(ax+14, ay-16, 3, 0, Math.PI*2);
    ctx.fill();
  } else if (agent.state === "done") {
    ctx.fillStyle = "#4ecca3";
    ctx.beginPath();
    ctx.arc(ax+14, ay-16, 3, 0, Math.PI*2);
    ctx.fill();
  }
}

function wordWrap(text, maxLen) {
  const words = text.split(' ');
  const lines = [];
  let line = '';
  words.forEach(w => {
    if ((line + ' ' + w).length > maxLen) {
      lines.push(line);
      line = w;
    } else line = line ? line + ' ' + w : w;
  });
  if (line) lines.push(line);
  return lines.length ? lines : [''];
}

function updateAgents() {
  Object.entries(agents).forEach(([name, a]) => {
    a.x += (a.targetX - a.x) * 0.05;
    a.y += (a.targetY - a.y) * 0.05;
    if (Math.abs(a.x - a.targetX) < 0.5) a.x = a.targetX;
    if (Math.abs(a.y - a.targetY) < 0.5) a.y = a.targetY;
    if (a.sayingTimer > 0) a.sayingTimer--;
  });
}

function render() {
  drawOffice();
  Object.entries(agents).forEach(([name, agent]) => {
    drawAgent(name, agent);
  });
  updateAgents();
  requestAnimationFrame(render);
}

// polyfill roundRect
if (!CanvasRenderingContext2D.prototype.roundRect) {
  CanvasRenderingContext2D.prototype.roundRect = function(x,y,w,h,r) {
    this.moveTo(x+r, y);
    this.arcTo(x+w, y, x+w, y+h, r);
    this.arcTo(x+w, y+h, x, y+h, r);
    this.arcTo(x, y+h, x, y, r);
    this.arcTo(x, y, x+w, y, r);
  };
}

function moveAgentTo(name, tileX, tileY) {
  const a = agents[name];
  if (!a) return;
  a.targetX = tileX * T + T;
  a.targetY = tileY * T + T;
}

function moveAgentToRoom(name, roomKey) {
  const r = ROOMS[roomKey];
  if (r) moveAgentTo(name, r.x + Math.floor(r.w/2), r.y + Math.floor(r.h/2));
}

function sayAgent(name, text) {
  const a = agents[name];
  if (!a) return;
  a.saying = text;
  a.sayingTimer = 150;
  a.state = "working";
}

function setAgentIdle(name) {
  const a = agents[name];
  if (a) a.state = "idle";
}

function setAgentDone(name) {
  const a = agents[name];
  if (a) a.state = "done";
}

function updateStatusBar(agentName, text) {
  const bar = document.getElementById('statusBar');
  const a = agents[agentName];
  if (!a) return;
  const html = Object.entries(agents).map(([n, ag]) => {
    const dotClass = ag.state === "working" ? "working" : ag.state === "done" ? "done" : "idle";
    return `<span><span class="dot ${dotClass}"></span>${ag.emoji} ${n}</span>`;
  }).join('');
  bar.innerHTML = html;
}

// SSE
function startTask() {
  const input = document.getElementById('taskInput');
  const task = input.value.trim();
  if (!task) return;
  const btn = document.getElementById('runBtn');
  btn.disabled = true;

  // move all to meeting
  Object.keys(agents).forEach(name => {
    moveAgentToRoom(name, "meeting");
    agents[name].state = "idle";
    agents[name].saying = "";
  });
  updateStatusBar();

  const logDiv = document.getElementById('log');
  logDiv.innerHTML = '';
  logDiv.style.display = 'block';

  const evtSrc = new EventSource('/stream?task=' + encodeURIComponent(task));

  evtSrc.onmessage = function(e) {
    const data = JSON.parse(e.data);

    if (data.type === 'message') {
      const name = data.name;
      const agent = agents[name];
      if (agent) {
        // move agent up front and speak
        if (data.role === "Takim Lideri") moveAgentToRoom(name, "meeting");
        sayAgent(name, data.message.substring(0, 100));
        updateStatusBar(name);

        // log
        const row = document.createElement('div');
        row.className = 'log-msg';
        row.innerHTML = `<b>${data.emoji} ${name}:</b> ${escapeHtml(data.message.substring(0, 120))}`;
        logDiv.appendChild(row);
        logDiv.scrollTop = logDiv.scrollHeight;
      }
    }
    else if (data.type === 'summary') {
      Object.keys(agents).forEach(name => setAgentDone(name));
      updateStatusBar();
      const row = document.createElement('div');
      row.className = 'log-msg';
      row.style.color = '#4ecca3';
      row.textContent = 'Gorev tamamlandi!';
      logDiv.appendChild(row);
    }
    else if (data.type === 'done') {
      btn.disabled = false;
      evtSrc.close();
    }
    else if (data.type === 'error') {
      btn.disabled = false;
      evtSrc.close();
    }
  };

  evtSrc.onerror = function() {
    btn.disabled = false;
    evtSrc.close();
  };
}

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;')
          .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// send on enter
document.getElementById('taskInput').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') startTask();
});

// init
render();
updateStatusBar();
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
