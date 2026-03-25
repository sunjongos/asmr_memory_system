import asyncio
import json
import argparse
import sys
import logging
import os

import httpx

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .core import ASMRParallelOrchestrator
from .port_5050_bridge import Port5050Bridge, Port5050Error
from .dr_claw_search import DrClawSearchOrchestrator
from .luca_observer import LucaMemoryObserver
from .ontology_asmr import OntologyASMRSearcher

# Shared httpx client for Gemini API calls (connection pooling)
_gemini_client: httpx.AsyncClient | None = None


async def _get_gemini_client() -> httpx.AsyncClient:
    global _gemini_client
    if _gemini_client is None or _gemini_client.is_closed:
        _gemini_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
    return _gemini_client


async def _cleanup():
    """Close shared clients on exit."""
    global _gemini_client
    if _gemini_client and not _gemini_client.is_closed:
        await _gemini_client.aclose()


async def gemini_llm_call(system_prompt: str, user_prompt: str, json_schema: dict) -> str:
    """Call Gemini 2.5 Flash API with shared connection pool."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return json.dumps({"error": "GEMINI_API_KEY environment variable is not set."})

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={api_key}"
    )

    schema_str = json.dumps(json_schema, ensure_ascii=False) if json_schema else "{}"
    full_system_prompt = (
        system_prompt
        + "\n\n[CRITICAL INSTRUCTION]\n"
        "You MUST return ONLY a pure JSON string matching the schema below. "
        "No markdown fences (```json), no commentary, no extra text.\n"
        f"Schema: {schema_str}"
    )

    payload = {
        "systemInstruction": {"parts": [{"text": full_system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.2},
    }

    client = await _get_gemini_client()
    resp = await client.post(url, json=payload)
    if resp.status_code != 200:
        return json.dumps({"error": f"Gemini API Error {resp.status_code}: {resp.text[:300]}"})

    data = resp.json()
    try:
        text_response = data["candidates"][0]["content"]["parts"][0]["text"]

        # Strip markdown fences defensively
        text_response = text_response.strip()
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        if text_response.startswith("```"):
            text_response = text_response[3:]
        if text_response.endswith("```"):
            text_response = text_response[:-3]

        return text_response.strip()
    except (KeyError, IndexError):
        return json.dumps({"error": "Failed to parse Gemini API response structure"})


async def run_query(question: str):
    bridge = Port5050Bridge()
    try:
        print(f"\n[ASMR] Querying Port 5050 shared memory: '{question}'")

        core_engine = ASMRParallelOrchestrator(llm_async_callable=gemini_llm_call)
        dr_claw = DrClawSearchOrchestrator(orchestrator=core_engine, bridge=bridge)

        result = await dr_claw.analyze_from_5050_memory(question)

        print("\n[ASMR] Analysis Result (JSON):")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Port5050Error as e:
        print(f"\n[ASMR ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await bridge.close()
        await _cleanup()


async def run_observe(log_text: str):
    bridge = Port5050Bridge()
    try:
        print(f"\n[ASMR] Observer analyzing session log ({len(log_text)} chars)...")

        core_engine = ASMRParallelOrchestrator(llm_async_callable=gemini_llm_call)
        observer = LucaMemoryObserver(orchestrator=core_engine, bridge=bridge)

        result = await observer.process_session_log(log_text)

        print("\n[ASMR] Observer Result (JSON):")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Port5050Error as e:
        print(f"\n[ASMR ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await bridge.close()
        await _cleanup()


async def run_ontology(question: str):
    bridge = Port5050Bridge()
    try:
        print(f"\n[ASMR] Ontology graph traversal for: '{question}'")

        core_engine = ASMRParallelOrchestrator(llm_async_callable=gemini_llm_call)
        searcher = OntologyASMRSearcher(orchestrator=core_engine, bridge=bridge)

        result = await searcher.traverse_from_5050_memory(question)

        print("\n[ASMR] Ontology Traversal Result (JSON):")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Port5050Error as e:
        print(f"\n[ASMR ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await bridge.close()
        await _cleanup()


async def run_health():
    bridge = Port5050Bridge()
    try:
        is_healthy = await bridge.health_check()
        gemini_key = bool(os.environ.get("GEMINI_API_KEY"))

        status = {
            "port_5050": "OK" if is_healthy else "UNREACHABLE",
            "gemini_api_key": "SET" if gemini_key else "MISSING",
            "ready": is_healthy and gemini_key,
        }
        print(json.dumps(status, indent=2))

        if not status["ready"]:
            sys.exit(1)
    finally:
        await bridge.close()


def main():
    parser = argparse.ArgumentParser(
        description="ASMR Memory System - Production CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m asmr_memory_system query \"What caused the patient's headache?\"\n"
            "  python -m asmr_memory_system observe \"Today we discussed...\"\n"
            "  python -m asmr_memory_system ontology \"Relationship between metformin and kidney function\"\n"
            "  python -m asmr_memory_system health\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. Query (medical search via Dr.Claw 3-agent team)
    p_query = subparsers.add_parser(
        "query",
        help="Run 3-agent medical analysis + Arbiter cross-validation on Port 5050 memory",
    )
    p_query.add_argument("question", type=str, help="Medical or general question")

    # 2. Observe (session log analysis + auto-ingest)
    p_observe = subparsers.add_parser(
        "observe",
        help="Analyze session log with 3 observer agents and save insights to Port 5050",
    )
    p_observe.add_argument("log", type=str, help="Session text or log content")

    # 3. Ontology (knowledge graph traversal)
    p_ontology = subparsers.add_parser(
        "ontology",
        help="Traverse knowledge graph with Edge Interpreter + Pathfinder agents",
    )
    p_ontology.add_argument("question", type=str, help="Ontology/graph traversal query")

    # 4. Health check
    subparsers.add_parser(
        "health",
        help="Check Port 5050 connectivity and GEMINI_API_KEY status",
    )

    args = parser.parse_args()

    if args.command == "query":
        asyncio.run(run_query(args.question))
    elif args.command == "observe":
        asyncio.run(run_observe(args.log))
    elif args.command == "ontology":
        asyncio.run(run_ontology(args.question))
    elif args.command == "health":
        asyncio.run(run_health())


if __name__ == "__main__":
    main()
