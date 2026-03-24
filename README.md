# n8n Workflow Generator

AI-powered n8n workflow builder. Describe your automation in plain text, get a ready-to-import workflow JSON.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## What it does

1. You describe an automation in plain text (English or Turkish)
2. AI generates a complete n8n workflow JSON
3. You import the JSON into n8n and configure credentials
4. Your automation is live

## Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USER/n8n-workflow-generator.git
cd n8n-workflow-generator

# 2. Install
pip install -r requirements.txt

# 3. Set your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 4. Run
python server.py
```

Open **http://localhost:8000** - that's it.

## One-line setup

```bash
git clone https://github.com/YOUR_USER/n8n-workflow-generator.git && cd n8n-workflow-generator && pip install -r requirements.txt && cp .env.example .env && echo "ANTHROPIC_API_KEY=your-key-here" > .env && python server.py
```

## Features

| Feature | Description |
|---------|-------------|
| **AI Chat** | Describe automation in plain text, get workflow JSON |
| **10 Templates** | Pre-built workflows (Telegram bot, scraper, CRM, etc.) |
| **60+ Node Types** | All major n8n integrations supported |
| **2000+ Searchable Workflows** | Search real community workflows |
| **Web UI** | Clean dark interface with copy/download buttons |
| **Ready-Made Workflows** | 3 production workflows included |
| **Deploy to n8n** | Push workflows directly to your n8n instance |
| **Modal.com Deploy** | One command cloud deployment |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/agent/chat` | Generate workflow from text |
| `GET` | `/agent/templates` | List all templates |
| `GET` | `/agent/nodes` | List available node types |
| `POST` | `/agent/build` | Build workflow from node spec |
| `POST` | `/agent/template` | Build from template |
| `POST` | `/n8n/deploy` | Deploy to n8n instance |
| `GET` | `/search/workflows` | Search 2000+ workflows |

## Example Usage

### Via Web UI
Open http://localhost:8000, type your automation, click Generate.

### Via API
```bash
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Telegram bot that answers with AI and logs to Google Sheets"}'
```

### Via Claude Code
```bash
# In your Claude Code session:
curl -s http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "your automation description"}' | jq .workflow_json > workflow.json
```

## Included Ready-Made Workflows

### 1. Muhasebe Veri Girme Otomasyonu
Email/webhook fatura -> AI OCR -> Google Sheets -> Telegram bildirim + haftalik KDV raporu

### 2. E-Ticaret Telegram Stok Kontrol
`/stok`, `/urunler`, `/siparis`, `/rapor`, `/fiyat` komutlari + dusuk stok uyarisi

### 3. YouTube Viral Content Factory
Apify viral arama -> Claude AI script -> fal.ai video -> FFmpeg -> YouTube upload

## Deploy to Cloud (Modal.com)

```bash
# 1. Install modal
pip install modal

# 2. Authenticate
modal token set --token-id YOUR_ID --token-secret YOUR_SECRET

# 3. Set secret
modal secret create anthropic-key ANTHROPIC_API_KEY=sk-ant-...

# 4. Deploy
modal deploy agent.py
```

Your agent will be live at `https://YOUR_USER--n8n-automation-agent-web-app.modal.run`

## Project Structure

```
n8n-workflow-generator/
├── server.py              # Local FastAPI server (main entry)
├── agent.py               # Modal.com cloud deployment
├── workflow_templates.py   # 60 node types + 10 templates + builder
├── workflow_search.py      # 2000+ workflow search engine
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── web/
│   └── index.html          # Web UI (dark theme, single file)
└── workflows/
    ├── muhasebe-veri-girme-otomasyon.json
    ├── eticaret-telegram-stok-kontrol.json
    └── youtube-automation-simple.json
```

## Requirements

- Python 3.11+
- An Anthropic API key (or OpenAI key)
- n8n instance (for importing workflows)

## License

MIT
