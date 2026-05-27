# CodeCrew

Multi-agent AI coding system. 8 AI agents sit around a table, each with a
specialized role, working together to complete your coding tasks.

## Agents

| Agent | Role | Expertise |
|-------|------|-----------|
| 🧠 Alp | Team Lead | Planning, architecture |
| 💻 Cem | Developer | Writing code |
| 👁️ Rusty | Code Reviewer | Quality control |
| 🧪 Testo | Test Engineer | Testing |
| 🐛 Bug | Bug Hunter | Edge cases |
| 🚀 Devina | DevOps | Deployment |
| 📖 Doc | Documentation | README, docs |
| 💡 Ideator | Creative Ideas | Alternatives |

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Set API key in .env file
# Get a free key: https://console.groq.com/keys

# Terminal
python main.py "create a calculator app"

# Web UI
python web_app.py
# Open http://localhost:8000
```

## Tech

- **API:** Groq (free, no credit card needed)
- **Model:** meta-llama/llama-4-scout-17b-16e-instruct
- **Backend:** Python
- **Web:** FastAPI + SSE
