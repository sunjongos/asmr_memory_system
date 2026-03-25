import json
import logging

from .core import ASMRAgent, ASMRParallelOrchestrator
from .port_5050_bridge import Port5050Bridge, Port5050Error

logger = logging.getLogger(__name__)


def get_luca_observer_agents() -> list[ASMRAgent]:
    """
    [Phase 1] Three background observer agents that silently update
    Luca's long-term memory from session logs.
    """

    preferences_agent = ASMRAgent(
        name="PreferencesAgent",
        system_prompt=(
            "You are a background ASMR observer agent silently watching the user's conversation log. "
            "Extract the user's work style, preferred tools, device environment, and coding conventions. "
            "Return an empty discovered_preferences array if nothing new is found."
        ),
        json_schema={
            "type": "object",
            "properties": {
                "discovered_preferences": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "e.g., 'Prefers Vanilla JS over React'",
                }
            },
        },
    )

    timeline_agent = ASMRAgent(
        name="TimelineAgent",
        system_prompt=(
            "You are the Timeline Agent governing temporal flow. "
            "Extract which tasks started and completed during this session, "
            "capturing the chronological and causal event flow. "
            "Skip idle chatter. Return an empty events array if no significant events found."
        ),
        json_schema={
            "type": "object",
            "properties": {
                "events": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "time_context": {"type": "string"},
                            "event_description": {"type": "string"},
                        },
                    },
                }
            },
        },
    )

    update_agent = ASMRAgent(
        name="UpdateAgent",
        system_prompt=(
            "You are the Forgetting Agent that detects when old facts are superseded by new ones. "
            "Find explicit policy/fact changes like 'we used to do A, but from now on we do B.' "
            "Return an empty superseded_facts array if no changes detected."
        ),
        json_schema={
            "type": "object",
            "properties": {
                "superseded_facts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "old_fact": {"type": "string"},
                            "new_fact": {"type": "string"},
                        },
                    },
                }
            },
        },
    )

    return [preferences_agent, timeline_agent, update_agent]


class LucaMemoryObserver:
    """
    Feed session transcripts to 3 observer agents in parallel.
    Results are serialized as proper JSON and ingested into Port 5050.
    """

    def __init__(self, orchestrator: ASMRParallelOrchestrator, bridge: Port5050Bridge = None):
        self.orchestrator = orchestrator
        self.bridge = bridge if bridge else Port5050Bridge()
        self.agents = get_luca_observer_agents()

    async def process_session_log(self, session_text: str):
        """Analyze session text with parallel agents, then ingest to 5050."""
        results = await self.orchestrator.run_parallel_analysis(self.agents, session_text)

        if results.get("orchestration_status") == "aborted":
            logger.warning("Observer aborted: context too short. Skipping ingest.")
            return results

        # Serialize as proper JSON (not Python repr)
        summary_payload = json.dumps(
            results.get("agent_results", {}),
            indent=2,
            ensure_ascii=False,
        )

        try:
            await self.bridge.ingest_memory(
                summary_payload,
                title="Luca ASMR Observer Insight",
                agent_id="Luca_ASMR_Observer",
            )
            results["ingest_status"] = "success"
        except Port5050Error as e:
            logger.error(f"Failed to ingest observer results: {e}")
            results["ingest_status"] = f"failed: {e}"

        return results
