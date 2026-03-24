"""
n8n Automation Agent - Modal.com'da surekli calisan AI agent.
Prompt ile istek atildiginda n8n workflow'lari olusturur, yonetir ve calistirir.

Kullanim:
  - POST /agent/chat  -> dogal dilde otomasyon istegi
  - POST /agent/build -> dogrudan workflow olusturma
  - GET  /agent/templates -> hazir sablonlari listele
  - GET  /agent/nodes -> kullanilabilir node tiplerini listele
  - POST /n8n/deploy -> workflow'u n8n instance'a deploy et
  - GET  /health -> saglik kontrolu
"""

import modal
import json
import os
from typing import Optional

# Modal app definition
app = modal.App("n8n-automation-agent")

# Docker image with all dependencies
agent_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "httpx>=0.26.0",
        "pydantic>=2.5.0",
        "anthropic>=0.40.0",
        "openai>=1.12.0",
    )
    .add_local_file("workflow_templates.py", "/app/workflow_templates.py")
    .add_local_file("workflow_search.py", "/app/workflow_search.py")
)



# ============================================================================
# AI Workflow Builder - Claude/OpenAI powered
# ============================================================================

SYSTEM_PROMPT = """Sen bir n8n otomasyon uzmanissin. Kullanicinin dogal dilde ifade ettigi otomasyon ihtiyaclarini n8n workflow JSON'larina donusturursun.

## Yeteneklerin:
1. Kullanicinin istegini analiz et
2. Uygun n8n node'larini sec
3. Tam calisir n8n workflow JSON'u olustur
4. Workflow'u acikla ve optimize et

## Kullanilabilir Node Tipleri:
### Triggerlar:
- webhook: HTTP istek alir (POST/GET)
- schedule: Zamanlanmis calisma (cron)
- telegram_trigger: Telegram mesajlarini dinler
- email_trigger: Email geldiginde tetiklenir
- manual: Manuel calistirma

### AI/LLM:
- openai_chat: OpenAI GPT modelleri
- ai_agent: Langchain tabanli AI agent

### HTTP/API:
- http_request: Herhangi bir API'ye istek atar
- graphql: GraphQL sorgusu calistirir

### Veri Isleme:
- set: Veri alanlari ayarlar
- code: JavaScript/Python kodu calistirir
- function: JavaScript fonksiyonu
- merge: Veri birlestirme
- filter: Filtreleme
- sort: Siralama
- aggregate: Gruplama
- remove_duplicates: Tekrarlari kaldir
- split_in_batches: Parcali isleme

### Mantik/Akis:
- if: Kosullu dallama
- switch: Coklu dallama
- wait: Bekleme
- execute_workflow: Baska workflow calistir
- respond_to_webhook: Webhook cevabi

### Iletisim:
- telegram_send: Telegram mesaj gonder
- slack: Slack mesaj gonder
- discord: Discord mesaj gonder
- gmail_send: Gmail ile mail gonder
- email_send: SMTP ile mail gonder
- whatsapp: WhatsApp mesaj gonder

### Veritabani:
- postgres: PostgreSQL
- mysql: MySQL
- mongodb: MongoDB
- redis: Redis
- supabase: Supabase

### Bulut/Depolama:
- google_sheets: Google Sheets
- google_drive: Google Drive
- google_docs: Google Docs
- notion: Notion
- airtable: Airtable
- aws_s3: AWS S3

### Sosyal Medya:
- twitter: Twitter/X
- linkedin: LinkedIn

### CRM:
- hubspot: HubSpot
- pipedrive: Pipedrive

### E-ticaret:
- shopify: Shopify
- stripe: Stripe
- woocommerce: WooCommerce

### Proje Yonetimi:
- github: GitHub
- jira: Jira
- trello: Trello
- asana: Asana

### Dosya:
- read_binary_file: Dosya oku
- write_binary_file: Dosya yaz
- extract_from_file: PDF/CSV'den veri cikar
- convert_to_file: Dosya formatina donustur

### Web:
- rss_feed: RSS okuma
- html_extract: HTML'den veri cikar

## CIKTI FORMATI:
Her zaman su JSON formatinda cevap ver:
```json
{
  "workflow_name": "Workflow adi",
  "description": "Kisaca ne yapar",
  "nodes": [
    {"key": "node_tipi", "name": "Node Adi", "params": {...}},
    ...
  ],
  "connections": [[0, 1], [1, 2], ...],
  "tags": ["tag1", "tag2"],
  "setup_notes": "Kurulum icin gerekli bilgiler (API key'ler, credential'lar vs.)",
  "estimated_complexity": "low|medium|high"
}
```

## KURALLAR:
1. Her workflow'un bir trigger node'u olmali (ilk node)
2. Baglantilari mantikli sec - veri akisi olmali
3. Hata yonetimi icin gerekirse error handler ekle
4. Karmasik islemler icin Code node kullan
5. Parametre olarak credential bilgilerini GERCEK deger koyma, placeholder kullan
6. Her node icin aciklayici isim ver
7. Turkce isimler kullanabilirsin
"""


def call_ai(prompt: str, api_key: str, provider: str = "anthropic") -> str:
    """Call AI model to generate workflow specification."""
    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
    else:
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=4096,
        )
        return response.choices[0].message.content


def parse_ai_response(response_text: str) -> dict:
    """Parse AI response to extract workflow spec JSON."""
    # Try to find JSON block in response
    import re

    # Look for ```json ... ``` blocks
    json_match = re.search(r'```json\s*\n?(.*?)\n?\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find raw JSON object
    json_match = re.search(r'\{[^{}]*"workflow_name"[^{}]*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # Try parsing entire response as JSON
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    return {"error": "Could not parse AI response", "raw_response": response_text}


# ============================================================================
# FastAPI Application on Modal
# ============================================================================

@app.function(
    image=agent_image,
    secrets=[
        modal.Secret.from_name("anthropic-key"),
    ],
    keep_warm=1,
    timeout=300,
    allow_concurrent_inputs=20,
)
@modal.asgi_app()
def web_app():
    """Main FastAPI application served on Modal."""
    import sys
    sys.path.insert(0, "/app")

    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import List, Dict, Any
    from workflow_templates import (
        build_custom_workflow,
        build_workflow_from_template,
        get_available_templates,
        get_available_nodes,
        search_templates,
        NODE_REGISTRY,
        WORKFLOW_TEMPLATES,
    )

    api = FastAPI(
        title="n8n Automation Agent",
        description="AI-powered n8n workflow builder. Dogal dilde otomasyon istegi gonder, hazir workflow al.",
        version="1.0.0",
    )

    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Models ---
    class ChatRequest(BaseModel):
        message: str
        provider: str = "anthropic"  # "anthropic" or "openai"
        api_key: Optional[str] = None  # Override env var

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

    # --- Search Engine Init ---
    try:
        from workflow_search import WorkflowSearchEngine
        search_engine = WorkflowSearchEngine()
    except Exception:
        search_engine = None

    # --- Endpoints ---

    @api.get("/health")
    async def health():
        return {
            "status": "healthy",
            "service": "n8n-automation-agent",
            "version": "1.0.0",
            "workflow_db_available": search_engine.is_available if search_engine else False,
            "capabilities": [
                "chat - Dogal dilde otomasyon istegi",
                "build - Manuel workflow olusturma",
                "templates - Hazir sablonlar",
                "search - 2000+ gercek workflow'da arama",
                "deploy - n8n'e deploy etme",
            ],
        }

    @api.get("/search/workflows")
    async def search_workflows(
        q: str = "",
        trigger: str = "all",
        complexity: str = "all",
        limit: int = 20,
        offset: int = 0,
    ):
        """Search across 2000+ real-world n8n workflows."""
        if not search_engine or not search_engine.is_available:
            raise HTTPException(status_code=503, detail="Workflow database not available")
        results, total = search_engine.search(
            query=q,
            trigger_filter=trigger,
            complexity_filter=complexity,
            limit=limit,
            offset=offset,
        )
        return {"results": results, "total": total, "query": q}

    @api.get("/search/similar")
    async def find_similar(description: str, limit: int = 5):
        """Find workflows similar to a description."""
        if not search_engine or not search_engine.is_available:
            raise HTTPException(status_code=503, detail="Workflow database not available")
        results = search_engine.find_similar_workflows(description, limit)
        return {"results": results, "total": len(results)}

    @api.get("/search/stats")
    async def search_stats():
        """Get workflow database statistics."""
        if not search_engine or not search_engine.is_available:
            raise HTTPException(status_code=503, detail="Workflow database not available")
        return search_engine.get_stats()

    @api.get("/search/integrations")
    async def list_integrations():
        """List all available integrations across workflows."""
        if not search_engine or not search_engine.is_available:
            raise HTTPException(status_code=503, detail="Workflow database not available")
        return {"integrations": search_engine.get_integrations_list()}

    @api.get("/search/workflow/{filename}")
    async def get_workflow_file(filename: str):
        """Get raw workflow JSON by filename."""
        if not search_engine or not search_engine.is_available:
            raise HTTPException(status_code=503, detail="Workflow database not available")
        wf = search_engine.get_workflow_json(filename)
        if not wf:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return wf

    @api.get("/agent/templates")
    async def list_templates():
        """List all available workflow templates."""
        return {
            "templates": get_available_templates(),
            "total": len(WORKFLOW_TEMPLATES),
        }

    @api.get("/agent/templates/search")
    async def search_template(q: str = ""):
        """Search workflow templates."""
        results = search_templates(q)
        return {"results": results, "total": len(results), "query": q}

    @api.get("/agent/nodes")
    async def list_nodes():
        """List all available n8n node types."""
        return {"nodes": get_available_nodes()}

    @api.post("/agent/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        """
        Ana endpoint: Dogal dilde otomasyon istegi gonder.
        AI otomatik olarak uygun n8n workflow'unu olusturur.

        Ornek: "Telegram'dan gelen mesajlari OpenAI ile cevapla ve Slack'e bildir"
        """
        try:
            # Get API key
            api_key = request.api_key
            if not api_key:
                if request.provider == "anthropic":
                    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
                else:
                    api_key = os.environ.get("OPENAI_API_KEY", "")

            if not api_key:
                raise HTTPException(
                    status_code=400,
                    detail=f"API key gerekli. {request.provider.upper()}_API_KEY environment variable'i veya request body'de api_key gonder.",
                )

            # First check if any template matches
            template_matches = search_templates(request.message)

            # Call AI to generate workflow
            ai_response = call_ai(request.message, api_key, request.provider)
            workflow_spec = parse_ai_response(ai_response)

            if "error" in workflow_spec:
                return ChatResponse(
                    message=f"AI cevabi isle nemedi. Ham cevap asagida:\n\n{ai_response}",
                    workflow_spec=workflow_spec,
                )

            # Build actual n8n workflow JSON
            try:
                workflow_json = build_custom_workflow(
                    name=workflow_spec.get("workflow_name", "AI Generated Workflow"),
                    nodes_list=workflow_spec.get("nodes", []),
                    connections_list=[tuple(c) for c in workflow_spec.get("connections", [])],
                    tags=workflow_spec.get("tags", []),
                )
            except Exception as e:
                workflow_json = None

            # Build explanation
            setup_notes = workflow_spec.get("setup_notes", "")
            complexity = workflow_spec.get("estimated_complexity", "medium")
            node_count = len(workflow_spec.get("nodes", []))

            message = f"""## {workflow_spec.get('workflow_name', 'Workflow')}

**Aciklama:** {workflow_spec.get('description', '')}
**Karmasiklik:** {complexity}
**Node Sayisi:** {node_count}

### Kurulum Notlari:
{setup_notes}

### Sonraki Adimlar:
1. Workflow JSON'unu n8n'e import edin
2. Gerekli credential'lari ayarlayin
3. Node parametrelerini durumunuza gore guncelleyin
4. Test edin ve aktif edin
"""

            if template_matches:
                message += f"\n**Not:** Bu istege benzer {len(template_matches)} hazir sablon da bulundu: {', '.join(m['name'] for m in template_matches[:3])}"

            return ChatResponse(
                message=message,
                workflow_json=workflow_json,
                workflow_spec=workflow_spec,
                template_used=template_matches[0]["key"] if template_matches else None,
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Bir hata olustu: {str(e)}")

    @api.post("/agent/build")
    async def build_workflow(request: BuildRequest):
        """Manually build a workflow from node specs."""
        try:
            workflow = build_custom_workflow(
                name=request.workflow_name,
                nodes_list=request.nodes,
                connections_list=[tuple(c) for c in request.connections],
                tags=request.tags,
            )
            return {
                "success": True,
                "workflow": workflow,
                "node_count": len(workflow["nodes"]),
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @api.post("/agent/template")
    async def build_from_template(request: TemplateRequest):
        """Build a workflow from a pre-built template."""
        try:
            workflow = build_workflow_from_template(
                request.template_key,
                request.custom_settings,
            )
            return {
                "success": True,
                "workflow": workflow,
                "template": request.template_key,
            }
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @api.post("/n8n/deploy")
    async def deploy_to_n8n(request: DeployRequest):
        """Deploy a workflow to a running n8n instance."""
        import httpx

        try:
            headers = {}
            if request.api_key:
                headers["X-N8N-API-KEY"] = request.api_key

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Create workflow
                response = await client.post(
                    f"{request.n8n_url}/api/v1/workflows",
                    json=request.workflow_json,
                    headers=headers,
                )

                if response.status_code not in (200, 201):
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"n8n API error: {response.text}",
                    )

                result = response.json()
                workflow_id = result.get("id")

                # Activate if requested
                if request.activate and workflow_id:
                    activate_response = await client.patch(
                        f"{request.n8n_url}/api/v1/workflows/{workflow_id}",
                        json={"active": True},
                        headers=headers,
                    )
                    if activate_response.status_code == 200:
                        result["active"] = True

                return {
                    "success": True,
                    "workflow_id": workflow_id,
                    "message": f"Workflow basariyla deploy edildi! ID: {workflow_id}",
                    "n8n_url": f"{request.n8n_url}/workflow/{workflow_id}",
                }

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail=f"n8n instance'a baglanilamadi: {request.n8n_url}",
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @api.get("/n8n/workflows")
    async def list_n8n_workflows(n8n_url: str = "http://localhost:5678", api_key: str = ""):
        """List workflows from a running n8n instance."""
        import httpx

        try:
            headers = {}
            if api_key:
                headers["X-N8N-API-KEY"] = api_key

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{n8n_url}/api/v1/workflows",
                    headers=headers,
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail=response.text)
                return response.json()
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail=f"n8n baglantisi basarisiz: {n8n_url}")

    @api.post("/n8n/execute/{workflow_id}")
    async def execute_workflow(
        workflow_id: str,
        n8n_url: str = "http://localhost:5678",
        api_key: str = "",
        data: Dict = None,
    ):
        """Execute a workflow on n8n."""
        import httpx

        try:
            headers = {}
            if api_key:
                headers["X-N8N-API-KEY"] = api_key

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{n8n_url}/api/v1/workflows/{workflow_id}/execute",
                    json=data or {},
                    headers=headers,
                )
                if response.status_code not in (200, 201):
                    raise HTTPException(status_code=response.status_code, detail=response.text)
                return response.json()
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail=f"n8n baglantisi basarisiz: {n8n_url}")

    return api


# ============================================================================
# n8n Self-Hosted Instance
# NOT: n8n icin ayri hosting oneriliyor (Railway/Render/VPS).
# Modal serverless yapisi, surekli calisan n8n icin ideal degil.
# n8n Cloud (n8n.io/cloud) veya Docker ile kendi sunucunuzda calistirin.
# ============================================================================


# ============================================================================
# CLI Entry Points
# ============================================================================

@app.local_entrypoint()
def main():
    """Local entry point for testing."""
    print("n8n Automation Agent")
    print("=" * 50)
    print("Deploy komutu: modal deploy agent.py")
    print("Test komutu:   modal serve agent.py")
    print()
    print("Endpoints:")
    print("  POST /agent/chat      - AI ile otomasyon olustur")
    print("  POST /agent/build     - Manuel workflow olustur")
    print("  POST /agent/template  - Sablondan workflow olustur")
    print("  GET  /agent/templates - Sablonlari listele")
    print("  GET  /agent/nodes     - Node tiplerini listele")
    print("  POST /n8n/deploy      - Workflow'u n8n'e deploy et")
    print("  GET  /n8n/workflows   - n8n workflow'larini listele")
    print("  POST /n8n/execute     - Workflow calistir")
