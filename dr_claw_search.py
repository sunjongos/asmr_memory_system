import logging

from .core import ASMRAgent, ASMRParallelOrchestrator
from .port_5050_bridge import Port5050Bridge, Port5050Error

logger = logging.getLogger(__name__)


def get_dr_claw_agents() -> list[ASMRAgent]:
    """
    [Phase 2] Three medical search agents for Dr.Claw diagnostic support.
    Extract facts, background context, and causal timelines from patient records.
    """

    fact_agent = ASMRAgent(
        name="FactAgent",
        system_prompt=(
            "You are the elite medical Fact Agent. "
            "Extract ONLY hard facts from patient records: vitals (blood glucose, BP, temperature, dosages), "
            "explicit prescriptions, official diagnoses, and lab results. "
            "Completely ignore emotions, opinions, and subjective context. "
            "If the input contains no medical facts, return an empty medical_facts array."
        ),
        json_schema={
            "type": "object",
            "properties": {
                "medical_facts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": ["vitals", "medication", "lab_result", "diagnosis"],
                            },
                            "fact_value": {"type": "string"},
                        },
                    },
                }
            },
        },
    )

    context_agent = ASMRAgent(
        name="ContextAgent",
        system_prompt=(
            "You are the medical Context Agent. "
            "Capture background information that numbers can't express: lifestyle (diet, sleep, exercise), "
            "family history, physician's subjective impressions, and patient complaints. "
            "This complements the Fact Agent by providing the 'why' behind the numbers. "
            "If no contextual information is found, return an empty patient_context array."
        ),
        json_schema={
            "type": "object",
            "properties": {
                "patient_context": {
                    "type": "array",
                    "items": {"type": "string"},
                }
            },
        },
    )

    causal_agent = ASMRAgent(
        name="CausalAgent",
        system_prompt=(
            "You are the Causal Agent tracking temporal flow and causality. "
            "Identify sequences like 'after event A (e.g., drug X started), symptom B appeared 3 days later.' "
            "Map symptom progression on a timeline and extract plausible cause-effect relationships. "
            "ONLY report relationships explicitly stated or strongly implied in the text. "
            "Never fabricate causal links. If none found, return an empty causality_timeline array."
        ),
        json_schema={
            "type": "object",
            "properties": {
                "causality_timeline": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "event_sequence": {
                                "type": "string",
                                "description": "e.g., Drug A started -> 3 days later headache onset",
                            },
                            "confidence": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                            },
                        },
                    },
                }
            },
        },
    )

    return [fact_agent, context_agent, causal_agent]


class DrClawSearchOrchestrator:
    """
    Medical query orchestrator: dispatches 3 search agents in parallel,
    then Arbiter cross-validates for contradictions.
    """

    def __init__(self, orchestrator: ASMRParallelOrchestrator, bridge: Port5050Bridge = None):
        self.orchestrator = orchestrator
        self.bridge = bridge if bridge else Port5050Bridge()
        self.agents = get_dr_claw_agents()

    async def analyze_patient_record(self, record_text: str):
        """Analyze directly provided EMR text or clinical log."""
        return await self.orchestrator.run_parallel_analysis(self.agents, record_text)

    async def analyze_from_5050_memory(self, question: str):
        """
        Fetch raw context from Port 5050, then run ASMR parallel analysis.
        Propagates Port5050Error with clear messages instead of silent failure.
        """
        logger.info(f"Fetching raw context from Port 5050 for: {question}")

        raw_memory_context = await self.bridge.fetch_raw_memory(
            question, agent_id="DrClaw_ASMR"
        )

        logger.info(
            f"Received {len(raw_memory_context)} chars from 5050. "
            f"Dispatching {len(self.agents)} agents + Arbiter..."
        )
        return await self.orchestrator.run_parallel_analysis(self.agents, raw_memory_context)
