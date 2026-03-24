"""
Local development server - Modal.com gerektirmeden lokalde calistirir.
Kullanim: python server.py
"""

import json
import os
import re
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from workflow_templates import (
    build_custom_workflow,
    build_workflow_from_template,
    get_available_templates,
    get_available_nodes,
    search_templates,
    NODE_REGISTRY,
    WORKFLOW_TEMPLATES,
)

# --- App ---

app = FastAPI(
    title="n8n Workflow Generator",
    description="AI-powered n8n workflow builder",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---

class ChatRequest(BaseModel):
    message: str
    provider: str = "anthropic"
    api_key: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    workflow_json: Optional[Dict] = None
    workflow_spec: Optional[Dict] = None
    template_used: Optional[str] = None

class BuildRequest(BaseModel):
    workflow_name: str
    nodes: List[Dict[str, Any]]
    connections: List[List[int]]
    tags: List[str] = []

class TemplateRequest(BaseModel):
    template_key: str
    custom_settings: Dict[str, Any] = {}

class DeployRequest(BaseModel):
    workflow_json: Dict[str, Any]
    n8n_url: str = "http://localhost:5678"
    api_key: str = ""
    activate: bool = False

# --- AI ---

def build_system_prompt():
    """Build system prompt dynamically from NODE_REGISTRY."""
    node_keys = sorted(NODE_REGISTRY.keys())
    node_list = "\n".join(f"  - {k}: {NODE_REGISTRY[k]['description']}" for k in node_keys)
    return f"""Sen bir n8n otomasyon uzmanissin. Kullanicinin istegini n8n workflow JSON'ina donusturursun.
Turkce ve Ingilizce istekleri anlayabilirsin.

KURALLAR:
1. SADECE asagidaki "key" degerlerini kullan. Baska key kullanma.
2. Her node icin "key" (asagidaki listeden), "name" (aciklayici isim) ve "params" (opsiyonel parametreler) ver.
3. "connections" listesinde node index'lerini kullan: [[0,1],[1,2]] gibi.
4. Cevabinda SADECE JSON olsun, aciklama veya markdown yazma.

CIKTI FORMATI:
{{
  "workflow_name": "Workflow Adi",
  "description": "Ne yapar (1 cumle)",
  "nodes": [
    {{"key": "schedule", "name": "Her Gun Calistir", "params": {{}}}},
    {{"key": "http_request", "name": "API Cagir", "params": {{"url": "https://example.com", "method": "GET"}}}}
  ],
  "connections": [[0, 1], [1, 2]],
  "tags": ["tag1", "tag2"],
  "setup_notes": "Kullanicinin yapmas gereken ayarlar (credential ekleme, URL degistirme vs.)",
  "estimated_complexity": "low|medium|high"
}}

KULLANILABILIR NODE TIPLERI (sadece bunlari kullan):
{node_list}

ONEMLI:
- Trigger node'u her zaman ilk sirada olmali (index 0).
- Email gondermek icin email_send (SMTP) veya gmail_send (Gmail API) kullan.
- AI islemleri icin openai_chat kullan.
- Telegram mesaj gondermek icin telegram_send, almak icin telegram_trigger kullan.
- Her workflow en az 2 node icermeli.
- params icinde n8n expression kullanabilirsin: ={{{{ $json.field }}}}"""

SYSTEM_PROMPT = build_system_prompt()


def call_ai(prompt: str, api_key: str, provider: str = "anthropic") -> str:
    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        r = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return r.content[0].text
    else:
        import openai
        client = openai.OpenAI(api_key=api_key)
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=4096,
        )
        return r.choices[0].message.content


def parse_ai_response(text: str) -> dict:
    text = re.sub(r'```json\s*\n?', '', text)
    text = re.sub(r'```\s*', '', text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r'\{[\s\S]*\}', text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return {"error": "Could not parse AI response", "raw": text}


# --- Search engine (optional) ---

try:
    from workflow_search import WorkflowSearchEngine
    search_engine = WorkflowSearchEngine()
except Exception:
    search_engine = None

# --- Endpoints ---

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "n8n-workflow-generator",
        "version": "1.0.0",
        "search_available": search_engine.is_available if search_engine else False,
    }

@app.get("/agent/templates")
async def list_templates():
    return {"templates": get_available_templates(), "total": len(WORKFLOW_TEMPLATES)}

@app.get("/agent/templates/search")
async def search_template(q: str = ""):
    results = search_templates(q)
    return {"results": results, "total": len(results)}

@app.get("/agent/nodes")
async def list_nodes():
    return {"nodes": get_available_nodes()}

@app.post("/agent/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    api_key = req.api_key
    if not api_key:
        api_key = os.environ.get(
            "ANTHROPIC_API_KEY" if req.provider == "anthropic" else "OPENAI_API_KEY", ""
        )
    if not api_key:
        raise HTTPException(400, f"Set {req.provider.upper()}_API_KEY in .env or send api_key in request body.")

    template_matches = search_templates(req.message)

    ai_text = call_ai(req.message, api_key, req.provider)
    spec = parse_ai_response(ai_text)

    if "error" in spec:
        return ChatResponse(message=f"Could not parse AI response.\n\n{ai_text}", workflow_spec=spec)

    try:
        wf_json = build_custom_workflow(
            name=spec.get("workflow_name", "AI Generated Workflow"),
            nodes_list=spec.get("nodes", []),
            connections_list=[tuple(c) for c in spec.get("connections", [])],
            tags=spec.get("tags", []),
        )
    except Exception as e:
        wf_json = None
        print(f"[WARN] build_custom_workflow failed: {e}")

    msg = f"""## {spec.get('workflow_name', 'Workflow')}

**Description:** {spec.get('description', '')}
**Complexity:** {spec.get('estimated_complexity', 'medium')}
**Nodes:** {len(spec.get('nodes', []))}

### Setup Notes:
{spec.get('setup_notes', '')}

### Next Steps:
1. Copy the JSON and import into n8n (Settings > Import)
2. Configure credentials for each service
3. Update node parameters for your use case
4. Test and activate
"""
    return ChatResponse(
        message=msg,
        workflow_json=wf_json,
        workflow_spec=spec,
        template_used=template_matches[0]["key"] if template_matches else None,
    )

@app.post("/agent/build")
async def build_workflow(req: BuildRequest):
    wf = build_custom_workflow(
        name=req.workflow_name,
        nodes_list=req.nodes,
        connections_list=[tuple(c) for c in req.connections],
        tags=req.tags,
    )
    return {"success": True, "workflow": wf}

@app.post("/agent/template")
async def build_from_template(req: TemplateRequest):
    try:
        wf = build_workflow_from_template(req.template_key, req.custom_settings)
        return {"success": True, "workflow": wf}
    except ValueError as e:
        raise HTTPException(404, str(e))

@app.post("/n8n/deploy")
async def deploy_to_n8n(req: DeployRequest):
    import httpx
    headers = {"X-N8N-API-KEY": req.api_key} if req.api_key else {}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{req.n8n_url}/api/v1/workflows", json=req.workflow_json, headers=headers)
        if r.status_code not in (200, 201):
            raise HTTPException(r.status_code, f"n8n error: {r.text}")
        result = r.json()
        wf_id = result.get("id")
        if req.activate and wf_id:
            await client.patch(f"{req.n8n_url}/api/v1/workflows/{wf_id}", json={"active": True}, headers=headers)
        return {"success": True, "workflow_id": wf_id, "url": f"{req.n8n_url}/workflow/{wf_id}"}

# Search endpoints (if workflow DB available)
@app.get("/search/workflows")
async def search_workflows(q: str = "", limit: int = 20):
    if not search_engine or not search_engine.is_available:
        raise HTTPException(503, "Workflow search DB not available")
    results, total = search_engine.search(query=q, limit=limit)
    return {"results": results, "total": total}

# Serve ready-made workflows
if os.path.isdir("workflows"):
    app.mount("/workflows", StaticFiles(directory="workflows"), name="workflows")

# Serve web UI
app.mount("/", StaticFiles(directory="web", html=True), name="web")


if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv
    load_dotenv()
    print("\n  n8n Workflow Generator")
    print("  http://localhost:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
