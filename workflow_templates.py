"""
n8n Workflow Template Library
Provides pre-built workflow templates and node definitions for the AI agent.
"""

import json
from typing import Dict, List, Any, Optional
import uuid


# ============================================================================
# n8n Node Type Registry - All common node types and their configurations
# ============================================================================

NODE_REGISTRY: Dict[str, Dict[str, Any]] = {
    # --- Triggers ---
    "webhook": {
        "type": "n8n-nodes-base.webhook",
        "category": "trigger",
        "description": "Receives HTTP requests (GET, POST, PUT, DELETE)",
        "default_params": {
            "httpMethod": "POST",
            "path": "webhook",
            "responseMode": "onReceived",
            "responseData": "allEntries",
        },
    },
    "schedule": {
        "type": "n8n-nodes-base.scheduleTrigger",
        "category": "trigger",
        "description": "Runs workflow on a schedule (cron)",
        "default_params": {
            "rule": {"interval": [{"field": "hours", "hoursInterval": 1}]}
        },
    },
    "cron": {
        "type": "n8n-nodes-base.cron",
        "category": "trigger",
        "description": "Runs workflow based on cron expression",
        "default_params": {
            "triggerTimes": {"item": [{"mode": "everyDay", "hour": 9, "minute": 0}]}
        },
    },
    "manual": {
        "type": "n8n-nodes-base.manualTrigger",
        "category": "trigger",
        "description": "Manual trigger for testing",
        "default_params": {},
    },
    "email_trigger": {
        "type": "n8n-nodes-base.emailReadImap",
        "category": "trigger",
        "description": "Triggers when new email arrives via IMAP",
        "default_params": {
            "mailbox": "INBOX",
            "format": "simple",
        },
    },
    "telegram_trigger": {
        "type": "n8n-nodes-base.telegramTrigger",
        "category": "trigger",
        "description": "Triggers on Telegram messages",
        "default_params": {"updates": ["*"], "additionalFields": {}},
    },

    # --- AI / LLM ---
    "openai": {
        "type": "@n8n/n8n-nodes-langchain.openAi",
        "category": "ai",
        "description": "OpenAI API - GPT models for text generation",
        "default_params": {
            "resource": "chat",
            "model": "gpt-4o-mini",
            "messages": {
                "values": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "={{ $json.message }}"},
                ]
            },
        },
    },
    "openai_chat": {
        "type": "n8n-nodes-base.openAi",
        "category": "ai",
        "description": "OpenAI Chat Completion",
        "default_params": {
            "resource": "chat",
            "operation": "create",
            "model": "gpt-4o-mini",
        },
    },
    "ai_agent": {
        "type": "@n8n/n8n-nodes-langchain.agent",
        "category": "ai",
        "description": "AI Agent with tools and memory",
        "default_params": {
            "agent": "conversationalAgent",
            "text": "={{ $json.message }}",
        },
    },

    # --- HTTP / API ---
    "http_request": {
        "type": "n8n-nodes-base.httpRequest",
        "category": "http",
        "description": "Make HTTP requests to any API",
        "default_params": {
            "method": "GET",
            "url": "",
            "options": {},
        },
    },
    "graphql": {
        "type": "n8n-nodes-base.graphql",
        "category": "http",
        "description": "Execute GraphQL queries",
        "default_params": {"endpoint": "", "query": ""},
    },

    # --- Data Processing ---
    "set": {
        "type": "n8n-nodes-base.set",
        "category": "data",
        "description": "Set/modify data fields",
        "default_params": {
            "mode": "manual",
            "duplicateItem": False,
            "assignments": {"assignments": []},
        },
    },
    "code": {
        "type": "n8n-nodes-base.code",
        "category": "data",
        "description": "Execute custom JavaScript/Python code",
        "default_params": {
            "mode": "runOnceForAllItems",
            "jsCode": "// Add your code here\nreturn items;",
        },
    },
    "function": {
        "type": "n8n-nodes-base.function",
        "category": "data",
        "description": "Execute JavaScript function",
        "default_params": {"functionCode": "return items;"},
    },
    "merge": {
        "type": "n8n-nodes-base.merge",
        "category": "data",
        "description": "Merge data from multiple inputs",
        "default_params": {"mode": "append"},
    },
    "split_in_batches": {
        "type": "n8n-nodes-base.splitInBatches",
        "category": "data",
        "description": "Split data into batches for processing",
        "default_params": {"batchSize": 10, "options": {}},
    },
    "aggregate": {
        "type": "n8n-nodes-base.aggregate",
        "category": "data",
        "description": "Aggregate items into a single item",
        "default_params": {"aggregate": "aggregateAllItemData", "options": {}},
    },
    "filter": {
        "type": "n8n-nodes-base.filter",
        "category": "data",
        "description": "Filter items based on conditions",
        "default_params": {"conditions": {"options": {"caseSensitive": True, "leftValue": ""}}},
    },
    "sort": {
        "type": "n8n-nodes-base.sort",
        "category": "data",
        "description": "Sort items by field",
        "default_params": {"sortFieldsUi": {"sortField": []}},
    },
    "remove_duplicates": {
        "type": "n8n-nodes-base.removeDuplicates",
        "category": "data",
        "description": "Remove duplicate items",
        "default_params": {"compare": "allFields"},
    },

    # --- Logic / Flow Control ---
    "if": {
        "type": "n8n-nodes-base.if",
        "category": "logic",
        "description": "Conditional branching (if/else)",
        "default_params": {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": ""},
                "conditions": [{"leftValue": "", "rightValue": "", "operator": {"type": "string", "operation": "equals"}}],
                "combinator": "and",
            }
        },
    },
    "switch": {
        "type": "n8n-nodes-base.switch",
        "category": "logic",
        "description": "Multi-way branching based on rules",
        "default_params": {
            "dataType": "string",
            "value1": "",
            "rules": {"rules": []},
        },
    },
    "wait": {
        "type": "n8n-nodes-base.wait",
        "category": "logic",
        "description": "Wait/delay execution",
        "default_params": {"amount": 1, "unit": "seconds"},
    },
    "execute_workflow": {
        "type": "n8n-nodes-base.executeWorkflow",
        "category": "logic",
        "description": "Execute another workflow",
        "default_params": {"source": "database", "workflowId": ""},
    },
    "respond_to_webhook": {
        "type": "n8n-nodes-base.respondToWebhook",
        "category": "logic",
        "description": "Send response back to webhook caller",
        "default_params": {
            "respondWith": "json",
            "responseBody": "={{ $json }}",
        },
    },
    "error_trigger": {
        "type": "n8n-nodes-base.errorTrigger",
        "category": "logic",
        "description": "Triggers when workflow errors occur",
        "default_params": {},
    },

    # --- Communication ---
    "telegram_send": {
        "type": "n8n-nodes-base.telegram",
        "category": "communication",
        "description": "Send Telegram messages",
        "default_params": {
            "operation": "sendMessage",
            "chatId": "",
            "text": "",
            "additionalFields": {},
        },
    },
    "slack": {
        "type": "n8n-nodes-base.slack",
        "category": "communication",
        "description": "Send Slack messages",
        "default_params": {
            "operation": "post",
            "channel": "",
            "text": "",
        },
    },
    "discord": {
        "type": "n8n-nodes-base.discord",
        "category": "communication",
        "description": "Send Discord messages",
        "default_params": {
            "operation": "sendMessage",
            "channelId": "",
            "content": "",
        },
    },
    "gmail_send": {
        "type": "n8n-nodes-base.gmail",
        "category": "communication",
        "description": "Send emails via Gmail",
        "default_params": {
            "operation": "send",
            "sendTo": "",
            "subject": "",
            "message": "",
            "options": {},
        },
    },
    "email_send": {
        "type": "n8n-nodes-base.emailSend",
        "category": "communication",
        "description": "Send emails via SMTP",
        "default_params": {
            "fromEmail": "",
            "toEmail": "",
            "subject": "",
            "text": "",
        },
    },
    "whatsapp": {
        "type": "n8n-nodes-base.whatsApp",
        "category": "communication",
        "description": "Send WhatsApp messages",
        "default_params": {
            "operation": "sendMessage",
            "phoneNumberId": "",
            "recipientPhoneNumber": "",
        },
    },

    # --- Databases ---
    "postgres": {
        "type": "n8n-nodes-base.postgres",
        "category": "database",
        "description": "PostgreSQL database operations",
        "default_params": {"operation": "executeQuery", "query": ""},
    },
    "mysql": {
        "type": "n8n-nodes-base.mySql",
        "category": "database",
        "description": "MySQL database operations",
        "default_params": {"operation": "executeQuery", "query": ""},
    },
    "mongodb": {
        "type": "n8n-nodes-base.mongoDb",
        "category": "database",
        "description": "MongoDB database operations",
        "default_params": {"operation": "find", "collection": ""},
    },
    "redis": {
        "type": "n8n-nodes-base.redis",
        "category": "database",
        "description": "Redis key-value store operations",
        "default_params": {"operation": "get", "key": ""},
    },
    "supabase": {
        "type": "n8n-nodes-base.supabase",
        "category": "database",
        "description": "Supabase (PostgreSQL + Auth + Storage)",
        "default_params": {"operation": "getAll", "tableId": ""},
    },

    # --- Cloud & Storage ---
    "google_sheets": {
        "type": "n8n-nodes-base.googleSheets",
        "category": "cloud",
        "description": "Google Sheets operations",
        "default_params": {
            "operation": "appendOrUpdate",
            "documentId": {"mode": "url", "value": ""},
            "sheetName": {"mode": "list", "value": ""},
        },
    },
    "google_drive": {
        "type": "n8n-nodes-base.googleDrive",
        "category": "cloud",
        "description": "Google Drive file operations",
        "default_params": {"operation": "list", "options": {}},
    },
    "google_docs": {
        "type": "n8n-nodes-base.googleDocs",
        "category": "cloud",
        "description": "Google Docs operations",
        "default_params": {"operation": "get"},
    },
    "notion": {
        "type": "n8n-nodes-base.notion",
        "category": "cloud",
        "description": "Notion database/page operations",
        "default_params": {
            "operation": "getAll",
            "resource": "databasePage",
        },
    },
    "airtable": {
        "type": "n8n-nodes-base.airtable",
        "category": "cloud",
        "description": "Airtable operations",
        "default_params": {"operation": "list"},
    },
    "aws_s3": {
        "type": "n8n-nodes-base.awsS3",
        "category": "cloud",
        "description": "AWS S3 storage operations",
        "default_params": {"operation": "getAll", "bucketName": ""},
    },

    # --- Social Media ---
    "twitter": {
        "type": "n8n-nodes-base.twitter",
        "category": "social",
        "description": "Twitter/X operations",
        "default_params": {"operation": "create", "text": ""},
    },
    "linkedin": {
        "type": "n8n-nodes-base.linkedIn",
        "category": "social",
        "description": "LinkedIn operations",
        "default_params": {"operation": "create"},
    },

    # --- CRM & Sales ---
    "hubspot": {
        "type": "n8n-nodes-base.hubspot",
        "category": "crm",
        "description": "HubSpot CRM operations",
        "default_params": {"operation": "getAll", "resource": "contact"},
    },
    "pipedrive": {
        "type": "n8n-nodes-base.pipedrive",
        "category": "crm",
        "description": "Pipedrive CRM operations",
        "default_params": {"operation": "getAll", "resource": "deal"},
    },

    # --- E-commerce ---
    "shopify": {
        "type": "n8n-nodes-base.shopify",
        "category": "ecommerce",
        "description": "Shopify store operations",
        "default_params": {"operation": "getAll", "resource": "order"},
    },
    "stripe": {
        "type": "n8n-nodes-base.stripe",
        "category": "ecommerce",
        "description": "Stripe payment operations",
        "default_params": {"operation": "getAll", "resource": "charge"},
    },
    "woocommerce": {
        "type": "n8n-nodes-base.wooCommerce",
        "category": "ecommerce",
        "description": "WooCommerce operations",
        "default_params": {"operation": "getAll", "resource": "order"},
    },

    # --- Project Management ---
    "github": {
        "type": "n8n-nodes-base.github",
        "category": "project",
        "description": "GitHub operations",
        "default_params": {"operation": "getAll", "resource": "issue"},
    },
    "jira": {
        "type": "n8n-nodes-base.jira",
        "category": "project",
        "description": "Jira issue operations",
        "default_params": {"operation": "getAll", "resource": "issue"},
    },
    "trello": {
        "type": "n8n-nodes-base.trello",
        "category": "project",
        "description": "Trello board/card operations",
        "default_params": {"operation": "getAll", "resource": "card"},
    },
    "asana": {
        "type": "n8n-nodes-base.asana",
        "category": "project",
        "description": "Asana task operations",
        "default_params": {"operation": "getAll", "resource": "task"},
    },

    # --- File Handling ---
    "read_binary_file": {
        "type": "n8n-nodes-base.readBinaryFile",
        "category": "file",
        "description": "Read file from disk",
        "default_params": {"filePath": ""},
    },
    "write_binary_file": {
        "type": "n8n-nodes-base.writeBinaryFile",
        "category": "file",
        "description": "Write file to disk",
        "default_params": {"fileName": "", "dataPropertyName": "data"},
    },
    "extract_from_file": {
        "type": "n8n-nodes-base.extractFromFile",
        "category": "file",
        "description": "Extract data from PDF, CSV, JSON, etc.",
        "default_params": {"operation": "csv"},
    },
    "convert_to_file": {
        "type": "n8n-nodes-base.convertToFile",
        "category": "file",
        "description": "Convert data to file format",
        "default_params": {"operation": "csv"},
    },

    # --- RSS & Web ---
    "rss_feed": {
        "type": "n8n-nodes-base.rssFeedRead",
        "category": "web",
        "description": "Read RSS/Atom feeds",
        "default_params": {"url": ""},
    },
    "html_extract": {
        "type": "n8n-nodes-base.htmlExtract",
        "category": "web",
        "description": "Extract data from HTML",
        "default_params": {"sourceData": "url", "url": "", "extractionValues": {"values": []}},
    },
}


# ============================================================================
# Pre-built Workflow Templates
# ============================================================================

WORKFLOW_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "lead_capture_crm": {
        "name": "Lead Capture to CRM",
        "description": "Captures leads from webhook/form and adds them to CRM with notification",
        "tags": ["lead-generation", "crm", "automation"],
        "nodes_config": [
            {"key": "webhook", "name": "Lead Form Webhook", "params": {"httpMethod": "POST", "path": "lead-capture"}},
            {"key": "set", "name": "Format Lead Data", "params": {}},
            {"key": "if", "name": "Check Required Fields", "params": {}},
            {"key": "http_request", "name": "Add to CRM", "params": {"method": "POST"}},
            {"key": "slack", "name": "Notify Sales Team", "params": {}},
            {"key": "respond_to_webhook", "name": "Return Success", "params": {}},
        ],
        "connections_map": [
            (0, 1), (1, 2), (2, 3), (3, 4), (2, 5),
        ],
    },
    "social_media_poster": {
        "name": "AI Social Media Content Generator",
        "description": "Generates social media content with AI and posts to multiple platforms",
        "tags": ["social-media", "ai", "content"],
        "nodes_config": [
            {"key": "schedule", "name": "Daily Schedule", "params": {"rule": {"interval": [{"field": "days", "daysInterval": 1}]}}},
            {"key": "openai_chat", "name": "Generate Content", "params": {}},
            {"key": "twitter", "name": "Post to Twitter", "params": {}},
            {"key": "linkedin", "name": "Post to LinkedIn", "params": {}},
            {"key": "telegram_send", "name": "Notify Admin", "params": {}},
        ],
        "connections_map": [
            (0, 1), (1, 2), (1, 3), (1, 4),
        ],
    },
    "email_autoresponder": {
        "name": "AI Email Auto-Responder",
        "description": "Reads incoming emails, classifies them with AI, and sends appropriate responses",
        "tags": ["email", "ai", "customer-support"],
        "nodes_config": [
            {"key": "email_trigger", "name": "New Email Received", "params": {}},
            {"key": "openai_chat", "name": "Classify Email", "params": {}},
            {"key": "switch", "name": "Route by Category", "params": {}},
            {"key": "openai_chat", "name": "Generate Response", "params": {}},
            {"key": "gmail_send", "name": "Send Reply", "params": {}},
            {"key": "slack", "name": "Escalate to Human", "params": {}},
        ],
        "connections_map": [
            (0, 1), (1, 2), (2, 3), (3, 4), (2, 5),
        ],
    },
    "data_sync": {
        "name": "Multi-System Data Sync",
        "description": "Syncs data between multiple systems on a schedule",
        "tags": ["data-sync", "integration", "scheduled"],
        "nodes_config": [
            {"key": "schedule", "name": "Hourly Sync", "params": {}},
            {"key": "http_request", "name": "Fetch Source Data", "params": {}},
            {"key": "code", "name": "Transform Data", "params": {}},
            {"key": "if", "name": "Check Changes", "params": {}},
            {"key": "http_request", "name": "Update Target", "params": {"method": "PUT"}},
            {"key": "slack", "name": "Report Sync Status", "params": {}},
        ],
        "connections_map": [
            (0, 1), (1, 2), (2, 3), (3, 4), (4, 5),
        ],
    },
    "telegram_ai_bot": {
        "name": "Telegram AI Chatbot",
        "description": "AI-powered Telegram bot that responds to messages using GPT",
        "tags": ["telegram", "ai", "chatbot"],
        "nodes_config": [
            {"key": "telegram_trigger", "name": "Telegram Message", "params": {}},
            {"key": "set", "name": "Extract Message", "params": {}},
            {"key": "openai_chat", "name": "AI Response", "params": {}},
            {"key": "telegram_send", "name": "Send Reply", "params": {}},
        ],
        "connections_map": [
            (0, 1), (1, 2), (2, 3),
        ],
    },
    "ecommerce_order_processor": {
        "name": "E-commerce Order Processor",
        "description": "Processes new orders, updates inventory, sends confirmations",
        "tags": ["ecommerce", "orders", "automation"],
        "nodes_config": [
            {"key": "webhook", "name": "New Order Webhook", "params": {"path": "new-order"}},
            {"key": "code", "name": "Validate Order", "params": {}},
            {"key": "postgres", "name": "Update Inventory", "params": {}},
            {"key": "gmail_send", "name": "Send Confirmation", "params": {}},
            {"key": "slack", "name": "Notify Warehouse", "params": {}},
            {"key": "google_sheets", "name": "Log Order", "params": {}},
        ],
        "connections_map": [
            (0, 1), (1, 2), (2, 3), (2, 4), (2, 5),
        ],
    },
    "web_scraper": {
        "name": "Scheduled Web Scraper",
        "description": "Scrapes websites on schedule, processes data, stores results",
        "tags": ["scraping", "data-collection", "scheduled"],
        "nodes_config": [
            {"key": "schedule", "name": "Daily Scrape", "params": {}},
            {"key": "http_request", "name": "Fetch Page", "params": {}},
            {"key": "code", "name": "Parse HTML", "params": {}},
            {"key": "remove_duplicates", "name": "Deduplicate", "params": {}},
            {"key": "google_sheets", "name": "Save Results", "params": {}},
        ],
        "connections_map": [
            (0, 1), (1, 2), (2, 3), (3, 4),
        ],
    },
    "monitoring_alerting": {
        "name": "System Monitoring & Alerting",
        "description": "Monitors APIs/services and sends alerts on failure",
        "tags": ["monitoring", "alerting", "devops"],
        "nodes_config": [
            {"key": "schedule", "name": "Check Every 5 Min", "params": {"rule": {"interval": [{"field": "minutes", "minutesInterval": 5}]}}},
            {"key": "http_request", "name": "Health Check", "params": {}},
            {"key": "if", "name": "Is Healthy?", "params": {}},
            {"key": "slack", "name": "Alert: Service Down!", "params": {}},
            {"key": "telegram_send", "name": "SMS Alert", "params": {}},
        ],
        "connections_map": [
            (0, 1), (1, 2), (2, 3), (3, 4),
        ],
    },
    "invoice_processor": {
        "name": "Invoice Processor",
        "description": "Processes invoices from email, extracts data with AI, updates accounting",
        "tags": ["invoicing", "accounting", "ai"],
        "nodes_config": [
            {"key": "email_trigger", "name": "Invoice Email", "params": {}},
            {"key": "extract_from_file", "name": "Extract PDF", "params": {}},
            {"key": "openai_chat", "name": "Parse Invoice Data", "params": {}},
            {"key": "google_sheets", "name": "Update Ledger", "params": {}},
            {"key": "slack", "name": "Notify Accounting", "params": {}},
        ],
        "connections_map": [
            (0, 1), (1, 2), (2, 3), (3, 4),
        ],
    },
    "customer_onboarding": {
        "name": "Customer Onboarding Flow",
        "description": "Automated customer onboarding with welcome emails and CRM updates",
        "tags": ["onboarding", "customer-success", "automation"],
        "nodes_config": [
            {"key": "webhook", "name": "New Customer Signup", "params": {"path": "onboarding"}},
            {"key": "set", "name": "Prepare Customer Data", "params": {}},
            {"key": "http_request", "name": "Create CRM Contact", "params": {"method": "POST"}},
            {"key": "gmail_send", "name": "Send Welcome Email", "params": {}},
            {"key": "slack", "name": "Notify CS Team", "params": {}},
            {"key": "wait", "name": "Wait 3 Days", "params": {"amount": 3, "unit": "days"}},
            {"key": "gmail_send", "name": "Send Follow-up", "params": {}},
        ],
        "connections_map": [
            (0, 1), (1, 2), (2, 3), (2, 4), (3, 5), (5, 6),
        ],
    },
}


# ============================================================================
# Workflow Builder Functions
# ============================================================================

def create_node(key: str, name: str, position: List[int], custom_params: Dict = None) -> Dict:
    """Create a single n8n node from the registry."""
    if key not in NODE_REGISTRY:
        raise ValueError(f"Unknown node type: {key}")

    node_def = NODE_REGISTRY[key]
    params = {**node_def["default_params"]}
    if custom_params:
        params.update(custom_params)

    node = {
        "id": str(uuid.uuid4()),
        "name": name,
        "type": node_def["type"],
        "position": position,
        "parameters": params,
        "typeVersion": 1,
    }

    return node


def build_workflow_from_template(template_key: str, custom_settings: Dict = None) -> Dict:
    """Build a complete n8n workflow JSON from a template."""
    if template_key not in WORKFLOW_TEMPLATES:
        raise ValueError(f"Unknown template: {template_key}")

    template = WORKFLOW_TEMPLATES[template_key]
    nodes = []
    x_start = 250
    y_start = 300
    x_step = 300

    for i, node_config in enumerate(template["nodes_config"]):
        x = x_start + (i * x_step)
        y = y_start + ((i % 2) * 100)  # Stagger vertically

        params = node_config.get("params", {})
        if custom_settings and node_config["key"] in custom_settings:
            params.update(custom_settings[node_config["key"]])

        node = create_node(
            key=node_config["key"],
            name=node_config["name"],
            position=[x, y],
            custom_params=params,
        )
        nodes.append(node)

    # Build connections
    connections = {}
    for src_idx, dst_idx in template["connections_map"]:
        src_name = nodes[src_idx]["name"]
        if src_name not in connections:
            connections[src_name] = {"main": [[]]}

        # Ensure enough output arrays
        while len(connections[src_name]["main"]) == 0:
            connections[src_name]["main"].append([])

        connections[src_name]["main"][0].append({
            "node": nodes[dst_idx]["name"],
            "type": "main",
            "index": 0,
        })

    workflow = {
        "name": template["name"],
        "nodes": nodes,
        "connections": connections,
        "active": False,
        "settings": {
            "executionOrder": "v1",
        },
        "tags": template.get("tags", []),
    }

    return workflow


def build_custom_workflow(
    name: str,
    nodes_list: List[Dict],
    connections_list: List[tuple],
    tags: List[str] = None,
) -> Dict:
    """Build a custom workflow from a list of node specs and connections.

    nodes_list: [{"key": "webhook", "name": "My Trigger", "params": {...}}, ...]
    connections_list: [(0, 1), (1, 2), ...] - tuples of (source_index, target_index)
    """
    nodes = []
    x_start = 250
    y_start = 300
    x_step = 300

    for i, node_spec in enumerate(nodes_list):
        x = x_start + (i * x_step)
        y = y_start + ((i % 3) * 120)

        node = create_node(
            key=node_spec["key"],
            name=node_spec.get("name", f"Node {i}"),
            position=[x, y],
            custom_params=node_spec.get("params", {}),
        )
        nodes.append(node)

    # Build connections
    connections = {}
    for src_idx, dst_idx in connections_list:
        src_name = nodes[src_idx]["name"]
        if src_name not in connections:
            connections[src_name] = {"main": [[]]}
        connections[src_name]["main"][0].append({
            "node": nodes[dst_idx]["name"],
            "type": "main",
            "index": 0,
        })

    workflow = {
        "name": name,
        "nodes": nodes,
        "connections": connections,
        "active": False,
        "settings": {"executionOrder": "v1"},
        "tags": tags or [],
    }

    return workflow


def get_available_templates() -> List[Dict]:
    """Return list of available templates with descriptions."""
    return [
        {
            "key": key,
            "name": t["name"],
            "description": t["description"],
            "tags": t["tags"],
        }
        for key, t in WORKFLOW_TEMPLATES.items()
    ]


def get_available_nodes() -> List[Dict]:
    """Return list of available node types grouped by category."""
    categories = {}
    for key, node in NODE_REGISTRY.items():
        cat = node["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "key": key,
            "type": node["type"],
            "description": node["description"],
        })
    return categories


def search_templates(query: str) -> List[Dict]:
    """Search templates by keyword."""
    query_lower = query.lower()
    results = []
    for key, t in WORKFLOW_TEMPLATES.items():
        searchable = f"{t['name']} {t['description']} {' '.join(t['tags'])}".lower()
        if query_lower in searchable:
            results.append({
                "key": key,
                "name": t["name"],
                "description": t["description"],
                "tags": t["tags"],
            })
    return results
