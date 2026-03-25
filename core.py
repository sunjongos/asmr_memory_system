import asyncio
import json
import logging
from typing import List, Dict, Any, Callable, Awaitable

logger = logging.getLogger(__name__)

EMPTY_CONTEXT_THRESHOLD = 20  # Minimum chars to consider context valid


class ASMRAgent:
    """Single-role ASMR agent definition."""

    def __init__(self, name: str, system_prompt: str, json_schema: Dict[str, Any] = None):
        self.name = name
        self.system_prompt = system_prompt
        self.json_schema = json_schema


class ASMRParallelOrchestrator:
    """
    Core parallel orchestrator that runs multiple ASMR agents concurrently
    via asyncio.gather(), then optionally cross-validates results with an
    Arbiter agent.
    """

    def __init__(self, llm_async_callable: Callable[[str, str, Dict], Awaitable[str]]):
        self.llm_async_callable = llm_async_callable

    async def _run_agent(self, agent: ASMRAgent, context_data: str) -> Dict[str, Any]:
        """Run a single agent and return structured result."""
        try:
            response_text = await self.llm_async_callable(
                agent.system_prompt,
                context_data,
                agent.json_schema,
            )

            try:
                result_data = json.loads(response_text)
            except json.JSONDecodeError:
                result_data = {"raw_text": response_text}

            return {
                "agent_name": agent.name,
                "status": "success",
                "data": result_data,
            }
        except Exception as e:
            logger.error(f"Agent {agent.name} failed: {e}")
            return {
                "agent_name": agent.name,
                "status": "error",
                "error": str(e),
            }

    async def run_parallel_analysis(
        self,
        agents: List[ASMRAgent],
        context_data: str,
        run_arbiter: bool = True,
    ) -> Dict[str, Any]:
        """
        Run all agents in parallel on the same context data.
        If run_arbiter=True, a 4th Arbiter agent cross-validates the results
        for contradictions and assigns a confidence score.
        """
        if not context_data or len(context_data.strip()) < EMPTY_CONTEXT_THRESHOLD:
            return {
                "orchestration_status": "aborted",
                "reason": f"Context data too short ({len(context_data.strip())} chars). "
                          f"Minimum {EMPTY_CONTEXT_THRESHOLD} chars required to prevent hallucination.",
                "agent_results": {},
            }

        tasks = [self._run_agent(agent, context_data) for agent in agents]
        results = await asyncio.gather(*tasks)

        agent_results = {}
        successful_count = 0
        for res in results:
            agent_results[res["agent_name"]] = res
            if res["status"] == "success":
                successful_count += 1

        merged_report = {
            "orchestration_status": "completed",
            "agents_total": len(agents),
            "agents_succeeded": successful_count,
            "agent_results": agent_results,
        }

        # Arbiter: cross-validate if at least 2 agents succeeded
        if run_arbiter and successful_count >= 2:
            arbiter_result = await self._run_arbiter(agent_results)
            merged_report["arbiter"] = arbiter_result

        return merged_report

    async def _run_arbiter(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        4th agent that reads all other agents' outputs and checks for
        contradictions, assigns overall confidence, and produces a synthesis.
        """
        arbiter = ASMRAgent(
            name="ArbiterAgent",
            system_prompt=(
                "You are the Arbiter Agent. You receive the outputs of multiple specialist agents "
                "who analyzed the same source data independently. Your job:\n"
                "1. Detect contradictions between agents (e.g., Agent A says X, Agent B implies not-X)\n"
                "2. Flag any agent output that looks like hallucination (claims not grounded in source)\n"
                "3. Produce a unified confidence score (high/medium/low) for the overall analysis\n"
                "4. Write a brief synthesis combining the strongest, non-contradictory findings\n"
                "Be strict. If agents agree, confidence is high. If they contradict, flag it."
            ),
            json_schema={
                "type": "object",
                "properties": {
                    "contradictions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "agent_a": {"type": "string"},
                                "claim_a": {"type": "string"},
                                "agent_b": {"type": "string"},
                                "claim_b": {"type": "string"},
                                "severity": {"type": "string", "enum": ["critical", "minor"]},
                            },
                        },
                    },
                    "hallucination_flags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "agent": {"type": "string"},
                                "suspicious_claim": {"type": "string"},
                                "reason": {"type": "string"},
                            },
                        },
                    },
                    "overall_confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    },
                    "synthesis": {
                        "type": "string",
                        "description": "Brief unified summary of the strongest findings",
                    },
                },
            },
        )

        # Serialize agent results as the arbiter's input
        arbiter_input = json.dumps(agent_results, indent=2, ensure_ascii=False)
        result = await self._run_agent(arbiter, arbiter_input)
        return result
