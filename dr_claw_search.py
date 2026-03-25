from .core import ASMRAgent, ASMRParallelOrchestrator
from .port_5050_bridge import Port5050Bridge

def get_dr_claw_agents() -> list[ASMRAgent]:
    """
    [Phase 2] Dr.Claw(Doctor Eye 등 의료/환자 데이터)의 진단을 보조하는 3개의 Search Agent를 반환합니다.
    환자의 기록 텍스트에서 팩트, 배경문맥, 인과관계를 입체적으로 추출합니다.
    """
    
    # 1. 팩트 데이터 추출 요원 (수치, 처방 내역 등 명확한 사실)
    fact_agent = ASMRAgent(
        name="FactAgent",
        system_prompt=(
            "너는 최정예 의료 사실 탐색 요원(Fact Agent)이야. "
            "주어진 환자 기록에서 수치(혈당, 혈압, 체온, 투여 용량 등)와 "
            "명시적인 처방 기록, 공식 진단명 등 명확한 '팩트'만 추출해. 환자의 감정이나 주관적 문맥은 완전히 무시해."
        ),
        json_schema={
            "type": "object",
            "properties": {
                "medical_facts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "enum": ["vitals", "medication", "lab_result", "diagnosis"]},
                            "fact_value": {"type": "string"}
                        }
                    }
                }
            }
        }
    )
    
    # 2. 배경 문맥 요원 (환자의 생활 습관, 소견 등)
    context_agent = ASMRAgent(
        name="ContextAgent",
        system_prompt=(
            "너는 의료 문맥 탐색 요원(Context Agent)이야. "
            "환자의 생활 습관(식단, 수면, 운동), 가족력, 그리고 주치의의 개인적인 소견이나 "
            "주관적인 호소 등 수치로 표현되기 힘든 '배경 정보'를 잡아내. 이를 통해 Fact 요원이 놓치는 맥락을 보완해."
        ),
        json_schema={
            "type": "object",
            "properties": {
                "patient_context": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            }
        }
    )
    
    # 3. 인과 관계 및 시계열 전담 요원
    causal_agent = ASMRAgent(
        name="CausalAgent",
        system_prompt=(
            "너는 시간의 흐름과 인과성을 추적하는 인과 요원(Causal Agent)이야. "
            "기록을 통해 'A라는 사건(예: 특정 약물 복용) 이후 B라는 증상(예: 두통 발현)이 생겼다'와 같은 "
            "증상의 흐름과 변화 양상을 시간축으로 정리하고, 가능한 선후관계를 추출해. 환각(할루시네이션)을 방지하기 위해 텍스트에 있는 선후관계만 기재해."
        ),
        json_schema={
            "type": "object",
            "properties": {
                "causality_timeline": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "event_sequence": {"type": "string", "description": "e.g., 약물 A 복용 -> 3일 뒤 두통 발현"},
                            "confidence": {"type": "string", "enum": ["high", "medium", "low"], "description": "명시적으로 적혀있을수록 high"}
                        }
                    }
                }
            }
        }
    )
    
    return [fact_agent, context_agent, causal_agent]

class DrClawSearchOrchestrator:
    """
    의료 질의나 긴 환자 기록이 들어오면, 3개의 Search Agent를 동시에 풀어
    가장 완벽한 입체적 데이터 모델(다차원 JSON)을 생성합니다.
    """
    def __init__(self, orchestrator: ASMRParallelOrchestrator, bridge: Port5050Bridge = None):
        self.orchestrator = orchestrator
        self.bridge = bridge if bridge else Port5050Bridge()
        self.agents = get_dr_claw_agents()
        
    async def analyze_patient_record(self, record_text: str):
        """직접 전달받은 환자의 EMR 텍스트나 진료 로그를 분석합니다."""
        results = await self.orchestrator.run_parallel_analysis(self.agents, record_text)
        return results

    async def analyze_from_5050_memory(self, question: str):
        """
        Port 5050 공유 장기 메모리에 질의하여 가져온 컨텍스트를
        기반으로 ASMR 인지 검색을 수행합니다. (가장 진보된 방식)
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Fetching raw context from Port 5050 for question: {question}")
        
        # 1. 기존 공유 메모리 서버에서 질의어 기반 1차 데이터 가져오기
        raw_memory_context = await self.bridge.fetch_raw_memory(question, agent_id="DrClaw_ASMR")
        
        if not raw_memory_context:
            return {"error": "5050 Port returned no context. Cannot run ASMR."}
            
        logger.info("Executing parallel ASMR agents over fetched memory...")
        # 2. 가져온 데이터를 3개의 에이전트가 사방에서 입체 분석
        results = await self.orchestrator.run_parallel_analysis(self.agents, raw_memory_context)
        return results
