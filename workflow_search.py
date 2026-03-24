"""
n8n Workflow Search Integration
Connects to the n8n-workflows repository's SQLite database for searching
4343+ real-world workflow templates.
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


class WorkflowSearchEngine:
    """Search engine for the n8n-workflows repository database."""

    def __init__(self, db_path: str = None, workflows_dir: str = None):
        if db_path is None:
            # Try common paths
            candidates = [
                os.path.join(os.path.dirname(__file__), "..", "n8n-workflows", "workflows.db"),
                os.path.join(os.path.dirname(__file__), "workflows.db"),
                "/app/workflows.db",
            ]
            for c in candidates:
                if os.path.exists(c):
                    db_path = c
                    break

        if workflows_dir is None:
            candidates = [
                os.path.join(os.path.dirname(__file__), "..", "n8n-workflows", "workflows"),
                os.path.join(os.path.dirname(__file__), "workflows"),
                "/app/workflows",
            ]
            for c in candidates:
                if os.path.exists(c):
                    workflows_dir = c
                    break

        self.db_path = db_path
        self.workflows_dir = workflows_dir
        self._db_available = db_path is not None and os.path.exists(db_path)

    @property
    def is_available(self) -> bool:
        return self._db_available

    def _get_conn(self) -> sqlite3.Connection:
        if not self._db_available:
            raise RuntimeError("Workflow database not available. Run indexing first.")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def search(
        self,
        query: str = "",
        trigger_filter: str = "all",
        complexity_filter: str = "all",
        integrations_filter: List[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Dict], int]:
        """Full-text search across 4343+ workflows."""
        conn = self._get_conn()

        where_conditions = []
        params = []

        if trigger_filter != "all":
            where_conditions.append("w.trigger_type = ?")
            params.append(trigger_filter)

        if complexity_filter != "all":
            where_conditions.append("w.complexity = ?")
            params.append(complexity_filter)

        if integrations_filter:
            for integration in integrations_filter:
                where_conditions.append("w.integrations LIKE ?")
                params.append(f'%"{integration}"%')

        if query.strip():
            base_query = """
                SELECT w.*, rank
                FROM workflows_fts fts
                JOIN workflows w ON w.id = fts.rowid
                WHERE workflows_fts MATCH ?
            """
            params.insert(0, query)
        else:
            base_query = """
                SELECT w.*, 0 as rank
                FROM workflows w
                WHERE 1=1
            """

        if where_conditions:
            base_query += " AND " + " AND ".join(where_conditions)

        # Count
        count_query = f"SELECT COUNT(*) as total FROM ({base_query}) t"
        cursor = conn.execute(count_query, params)
        total = cursor.fetchone()["total"]

        # Results
        if query.strip():
            base_query += " ORDER BY rank"
        else:
            base_query += " ORDER BY w.node_count DESC"

        base_query += f" LIMIT {limit} OFFSET {offset}"
        cursor = conn.execute(base_query, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            workflow = dict(row)
            workflow["integrations"] = json.loads(workflow.get("integrations") or "[]")
            raw_tags = json.loads(workflow.get("tags") or "[]")
            workflow["tags"] = [
                t.get("name", str(t)) if isinstance(t, dict) else str(t) for t in raw_tags
            ]
            results.append(workflow)

        conn.close()
        return results, total

    def get_workflow_json(self, filename: str) -> Optional[Dict]:
        """Load raw workflow JSON file."""
        if not self.workflows_dir:
            return None

        workflows_path = Path(self.workflows_dir)
        for subdir in workflows_path.iterdir():
            if subdir.is_dir():
                target = subdir / filename
                if target.exists():
                    with open(target, "r", encoding="utf-8") as f:
                        return json.load(f)
        return None

    def find_similar_workflows(self, description: str, limit: int = 5) -> List[Dict]:
        """Find workflows similar to a description using FTS."""
        # Extract key terms
        keywords = description.lower().split()
        # Remove common words
        stop_words = {
            "bir", "ve", "ile", "icin", "bu", "da", "de", "den", "dan",
            "the", "a", "an", "and", "or", "for", "to", "in", "on", "with",
            "is", "are", "was", "were", "be", "been", "being",
            "otomasyon", "workflow", "otomatik", "automation",
        }
        meaningful = [w for w in keywords if w not in stop_words and len(w) > 2]

        if not meaningful:
            return []

        query = " OR ".join(meaningful[:5])
        results, _ = self.search(query=query, limit=limit)
        return results

    def get_stats(self) -> Dict:
        """Get database statistics."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT COUNT(*) as total FROM workflows")
        total = cursor.fetchone()["total"]

        cursor = conn.execute(
            "SELECT trigger_type, COUNT(*) as count FROM workflows GROUP BY trigger_type"
        )
        triggers = {row["trigger_type"]: row["count"] for row in cursor.fetchall()}

        cursor = conn.execute(
            "SELECT complexity, COUNT(*) as count FROM workflows GROUP BY complexity"
        )
        complexity = {row["complexity"]: row["count"] for row in cursor.fetchall()}

        cursor = conn.execute("SELECT integrations FROM workflows WHERE integrations != '[]'")
        all_integrations = set()
        for row in cursor.fetchall():
            for i in json.loads(row["integrations"]):
                all_integrations.add(i)

        conn.close()
        return {
            "total_workflows": total,
            "triggers": triggers,
            "complexity": complexity,
            "unique_integrations": len(all_integrations),
            "top_integrations": sorted(all_integrations)[:30],
        }

    def get_integrations_list(self) -> List[str]:
        """Get all unique integrations across all workflows."""
        conn = self._get_conn()
        cursor = conn.execute("SELECT integrations FROM workflows WHERE integrations != '[]'")
        all_integrations = set()
        for row in cursor.fetchall():
            for i in json.loads(row["integrations"]):
                all_integrations.add(i)
        conn.close()
        return sorted(all_integrations)

    def search_by_integration(self, integration: str, limit: int = 20) -> List[Dict]:
        """Find all workflows using a specific integration."""
        results, _ = self.search(
            integrations_filter=[integration],
            limit=limit,
        )
        return results


def init_database_from_workflows(workflows_dir: str, db_path: str = "workflows.db"):
    """Initialize/rebuild the database from workflow JSON files.
    Use this when no database exists yet."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "n8n-workflows"))

    try:
        from workflow_db import WorkflowDatabase
        db = WorkflowDatabase(db_path=db_path)
        db.workflows_dir = workflows_dir
        stats = db.index_all_workflows(force_reindex=True)
        print(f"Database initialized: {stats}")
        return stats
    except ImportError:
        print("workflow_db.py not found. Manual indexing required.")
        return None


# Quick test
if __name__ == "__main__":
    engine = WorkflowSearchEngine()

    if not engine.is_available:
        print("Database not found. Building from n8n-workflows repo...")
        wf_dir = os.path.join(os.path.dirname(__file__), "..", "n8n-workflows", "workflows")
        db_path = os.path.join(os.path.dirname(__file__), "..", "n8n-workflows", "workflows.db")
        if os.path.exists(wf_dir):
            init_database_from_workflows(wf_dir, db_path)
            engine = WorkflowSearchEngine(db_path=db_path, workflows_dir=wf_dir)
        else:
            print("n8n-workflows directory not found.")
            exit(1)

    print("=== Workflow Search Engine ===")
    stats = engine.get_stats()
    print(f"Total workflows: {stats['total_workflows']}")
    print(f"Unique integrations: {stats['unique_integrations']}")
    print(f"Triggers: {stats['triggers']}")
    print()

    # Test search
    for q in ["telegram", "openai", "slack email", "shopify"]:
        results, total = engine.search(q, limit=3)
        print(f"Search '{q}': {total} results")
        for r in results[:3]:
            print(f"  - {r['name']} ({r['trigger_type']}, {r['node_count']} nodes)")
        print()
