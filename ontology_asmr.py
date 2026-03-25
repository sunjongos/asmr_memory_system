import logging

from .core import ASMRAgent, ASMRParallelOrchestrator
from .port_5050_bridge import Port5050Bridge, Port5050Error

logger = logging.getLogger(__name__)


def get_ontology_traversal_agents() -> list[ASMRAgent]:
    """
    [Phase 3] Knowledge graph traversal agents.
    Analyze text-serialized sub-graphs to interpret edges and suggest next hops.
    """

    edge_agent = ASMRAgent(
        name="EdgeInterpreterAgent",
        system_prompt=(
            "You are the Edge Interpreter Agent for knowledge graphs (ontologies). "
            "Analyze the relationships (Is-A, Has-A, Treated-By, Causes, etc.) between "
            "nodes in the given sub-graph. Explain what hints these relationships provide "
            "for the user's question or diagnosis. "
            "Return an empty inferred_relationships array if no meaningful relationships found."
        ),
        json_schema={
            "type": "object",
            "properties": {
                "inferred_relationships": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "node_A": {"type": "string"},
                            "relationship": {"type": "string"},
                            "node_B": {"type": "string"},
                            "insight": {"type": "string"},
                        },
                    },
                }
            },
        },
    )

    pathfinder_agent = ASMRAgent(
        name="PathfinderAgent",
        system_prompt=(
            "You are the Pathfinder Agent for knowledge graph navigation. "
            "Given the current sub-graph context, suggest which nodes to explore next (hop to). "
            "If information is insufficient, propose follow-up queries or related node expansions. "
            "Return an empty suggested_next_hops array if current information is sufficient."
        ),
        json_schema={
            "type": "object",
            "properties": {
                "suggested_next_hops": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "reason": {
                    "type": "string",
                    "description": "Why expand to those nodes?",
                },
            },
        },
    )

    return [edge_agent, pathfinder_agent]


class OntologyASMRSearcher:
    """
    Attach ASMR parallel reasoning to ontology knowledge graphs
    (Dr.Claw, NDB, or any domain graph).
    """

    def __init__(self, orchestrator: ASMRParallelOrchestrator, bridge: Port5050Bridge = None):
        self.orchestrator = orchestrator
        self.bridge = bridge if bridge else Port5050Bridge()
        self.agents = get_ontology_traversal_agents()

    async def traverse_subgraph(self, subgraph_json: str):
        """Read and reason over a specific sub-graph (JSON or Markdown format)."""
        return await self.orchestrator.run_parallel_analysis(self.agents, subgraph_json)

    async def traverse_from_5050_memory(self, question: str):
        """
        Fetch ontology-relevant context from Port 5050, then run
        Edge Interpreter + Pathfinder in parallel.
        """
        logger.info(f"Fetching ontology context from Port 5050 for: {question}")

        raw_context = await self.bridge.fetch_raw_memory(
            question, agent_id="Ontology_ASMR"
        )

        logger.info(
            f"Received {len(raw_context)} chars. "
            f"Dispatching {len(self.agents)} ontology agents + Arbiter..."
        )
        return await self.orchestrator.run_parallel_analysis(self.agents, raw_context)
