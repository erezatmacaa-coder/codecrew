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
<title>CodeCrew</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', monospace;
         background: #0d1117; color: #c9d1d9; }
  .container { max-width: 800px; margin: 0 auto; padding: 20px; }
  h1 { text-align: center; color: #58a6ff; margin: 20px 0; font-size: 1.8em; }
  .agents { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; margin: 15px 0; }
  .agent-tag { background: #21262d; padding: 4px 10px; border-radius: 12px;
               font-size: 0.82em; border: 1px solid #30363d; }
  .task-form { display: flex; gap: 10px; margin: 20px 0; }
  .task-form input { flex:1; padding: 12px 16px; border-radius: 8px;
                     border: 1px solid #30363d; background: #161b22;
                     color: #c9d1d9; font-size: 1em; }
  .task-form input:focus { outline: none; border-color: #58a6ff; }
  .task-form button { padding: 12px 24px; border-radius: 8px; border: none;
                      background: #238636; color: #fff; font-size: 1em;
                      cursor: pointer; font-weight: 600; }
  .task-form button:hover { background: #2ea043; }
  .task-form button:disabled { opacity: 0.5; cursor: not-allowed; }
  #log { margin-top: 20px; }
  .msg { margin: 10px 0; padding: 12px 16px; border-radius: 8px;
         border: 1px solid #21262d; background: #161b22; }
  .msg-header { font-weight: 600; margin-bottom: 6px; font-size: 0.95em; }
  .msg-body { line-height: 1.5; white-space: pre-wrap; font-size: 0.92em; }
  .loading { text-align: center; color: #8b949e; margin: 20px; display: none; }
  .summary { margin-top: 20px; padding: 16px; border-radius: 8px;
             background: #1c2333; border: 1px solid #58a6ff33; display: none;
             white-space: pre-wrap; line-height: 1.6; }
  .error { color: #f85149; text-align: center; padding: 20px; display: none; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
  .loading { animation: pulse 1.5s infinite; }
</style>
</head>
<body>
<div class="container">
  <h1>🧠 AI MASA</h1>
  <div class="agents">
    """ + "".join(f'<span class="agent-tag">{a["emoji"]} {a["name"]}</span>'
                  for a in AGENTS) + """
  </div>
  <form class="task-form" id="form" onsubmit="return runTask(event)">
    <input type="text" id="taskInput" placeholder="Bir görev tanımla..."
           autocomplete="off" autofocus>
    <button type="submit" id="runBtn">▶ Başlat</button>
  </form>
  <div class="loading" id="loading">🤖 Ajanlar çalışıyor...</div>
  <div id="log"></div>
  <div class="summary" id="summary"></div>
  <div class="error" id="error"></div>
</div>

<script>
async function runTask(e) {
  e.preventDefault();
  const task = document.getElementById('taskInput').value.trim();
  if (!task) return false;

  const log = document.getElementById('log');
  const loading = document.getElementById('loading');
  const summary = document.getElementById('summary');
  const error = document.getElementById('error');
  const btn = document.getElementById('runBtn');

  log.innerHTML = '';
  summary.style.display = 'none';
  error.style.display = 'none';
  loading.style.display = 'block';
  btn.disabled = true;

  const evtSource = new EventSource('/stream?task=' + encodeURIComponent(task));

  evtSource.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === 'message') {
      const div = document.createElement('div');
      div.className = 'msg';
      div.innerHTML = '<div class="msg-header">' + data.emoji + ' ' +
                      data.name + ' (' + data.role + ')</div>' +
                      '<div class="msg-body">' + escapeHtml(data.message) + '</div>';
      log.appendChild(div);
      div.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
    else if (data.type === 'summary') {
      summary.textContent = data.content;
      summary.style.display = 'block';
      summary.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
    else if (data.type === 'error') {
      error.textContent = data.content;
      error.style.display = 'block';
    }
    else if (data.type === 'done') {
      loading.style.display = 'none';
      btn.disabled = false;
      evtSource.close();
    }
  };

  evtSource.onerror = function() {
    loading.style.display = 'none';
    btn.disabled = false;
    evtSource.close();
  };

  return false;
}

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;')
          .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
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

        def on_message(agent_round):
            data = {
                "type": "message",
                "name": agent_round.agent_name,
                "emoji": agent_round.emoji,
                "role": agent_round.role,
                "message": agent_round.message,
            }
            yield {"event": "message", "data": json.dumps(data, ensure_ascii=False)}

        def collect():
            messages = []
            summary_data = None

            def handler(msg):
                msg_data = {
                    "type": "message",
                    "name": msg.agent_name,
                    "emoji": msg.emoji,
                    "role": msg.role,
                    "message": msg.message,
                }
                messages.append(msg_data)

            summary_text = orchestrator.run(task, on_message=handler)

            for msg in messages:
                yield {"event": "message", "data": json.dumps(msg, ensure_ascii=False)}

            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "summary",
                    "content": summary_text,
                }, ensure_ascii=False),
            }

            yield {
                "event": "message",
                "data": json.dumps({"type": "done"}),
            }

        return EventSourceResponse(collect())

    gen = await event_generator()
    return gen


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
