# n8n Workflow Generator

## Overview
AI-powered n8n workflow builder. Local server with web UI. Prompt -> n8n JSON.

## How to run
```bash
pip install -r requirements.txt
cp .env.example .env  # add ANTHROPIC_API_KEY
python server.py      # http://localhost:8000
```

## Key files
- `server.py` - Local FastAPI server, all endpoints, AI integration
- `agent.py` - Modal.com cloud deploy version
- `workflow_templates.py` - Node registry (60 types), templates (10), builder functions
- `workflow_search.py` - SQLite FTS5 search over 2000+ community workflows
- `web/index.html` - Single-file dark-theme web UI

## Architecture
- User sends prompt to `/agent/chat`
- Server calls Claude/OpenAI with n8n-specific system prompt
- AI returns structured JSON spec (nodes + connections)
- `build_custom_workflow()` converts spec to valid n8n import JSON
- Web UI displays result with copy/download options

## Adding new node types
Edit `NODE_REGISTRY` in `workflow_templates.py`. Each entry: key, type string, default params.

## Adding new templates
Edit `WORKFLOW_TEMPLATES` in `workflow_templates.py`. Each template: key, name, description, tags, nodes list, connections list.

## Workflows directory
`workflows/` contains ready-made n8n workflow JSONs that users can download directly from the web UI.
