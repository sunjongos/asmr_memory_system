from .core import ASMRAgent, ASMRParallelOrchestrator
from .port_5050_bridge import Port5050Bridge

def get_luca_observer_agents() -> list[ASMRAgent]:
    """
    [Phase 1] Luca의 장기 기억망을 배경에서 조용히 업데이트하는 3개의 Observer Agent를 반환합니다.
    """
    
    # 1. 선호도 및 환경 추출 요원
    preferences_agent = ASMRAgent(
        name="PreferencesAgent",
        system_prompt=(
            "너는 대표님의 대화 로그를 조용히 관찰하는 ASMR 배경 에이전트야. "
            "이 대화에서 대표님의 업무 스타일, 선호하는 툴, 기기 환경, 코딩 관습 등을 찾아내어 JSON으로 추출해. "
            "새로운 지식이 없다면 빈 리스트를 반환해."
        ),
        json_schema={
            "type": "object",
            "properties": {
                "discovered_preferences": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "e.g., 'React 대신 Vanilla JS와 CSS를 선호함'"
                }
            }
        }
    )
    
    # 2. 타임라인 정리 요원
    timeline_agent = ASMRAgent(
        name="TimelineAgent",
        system_prompt=(
            "너는 시간 흐름을 관장하는 타임라인 에이전트야. "
            "현재 세션에서 어떤 태스크가 언제 시작되었고 언제 완료되었는지 시간적/인과적 흐름을 추출해. "
            "명시적인 이벤트 변화가 있다면 기록하고, 단순 잡담이면 제외해."
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
                            "event_description": {"type": "string"}
                        }
                    }
                }
            }
        }
    )
    
    # 3. 업데이트(Forgetting) 요원
    update_agent = ASMRAgent(
        name="UpdateAgent",
        system_prompt=(
            "너는 기존의 낡은 상식을 지우고 새로운 사실로 덮어씌우는 업데이트 요원(Forgetting Agent)이야. "
            "대화 내용 중 '원래는 A였는데 이제부터 B로 하자'처럼 명시적인 정책/사실 변경이 발생하면 그 내역을 잡아내야 해."
        ),
        json_schema={
            "type": "object",
            "properties": {
                "superseded_facts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "old_fact": {"type": "string", "description": "이제는 폐기된 기존의 사실"},
                            "new_fact": {"type": "string", "description": "새롭게 대체된 사실"}
                        }
                    }
                }
            }
        }
    )
    
    return [preferences_agent, timeline_agent, update_agent]

class LucaMemoryObserver:
    """
    세션이 끝날 때, 정리된 대화록을 이 클래스에 넘기면 3개의 에이전트가 돌면서
    옵시디언이나 메인 장기기억 JSON을 업데이트할 수 있는 구조화된 데이터를 뱉습니다.
    이후 도출된 고순도 인사이트는 Port5050Bridge를 통해 메인에 Ingest됩니다.
    """
    def __init__(self, orchestrator: ASMRParallelOrchestrator, bridge: Port5050Bridge = None):
        self.orchestrator = orchestrator
        self.bridge = bridge if bridge else Port5050Bridge()
        self.agents = get_luca_observer_agents()
        
    async def process_session_log(self, session_text: str):
        """세션 텍스트를 입력받아 병렬 인지를 수행합니다."""
        results = await self.orchestrator.run_parallel_analysis(self.agents, session_text)
        
        # 3명의 요원이 정리한 내용을 5050 포트로 자동 Ingest (Save)
        summary_payload = str(results)
        await self.bridge.ingest_memory(summary_payload, title="Luca ASMR Observer Insight", agent_id="Luca_ASMR_Observer")
        
        return results
