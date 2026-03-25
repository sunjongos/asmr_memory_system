import asyncio
import json
import logging
from typing import List, Dict, Any, Callable, Awaitable

logger = logging.getLogger(__name__)

class ASMRAgent:
    """ASMR 단일 역할 에이전트의 정의입니다."""
    def __init__(self, name: str, system_prompt: str, json_schema: Dict[str, Any] = None):
        self.name = name
        self.system_prompt = system_prompt
        self.json_schema = json_schema

class ASMRParallelOrchestrator:
    """
    ASMR의 근간인 병렬 에이전트 연산을 통제하는 오케스트레이터입니다.
    여러 Agent 객체를 한 번에 비동기(async)로 실행하고, 결과를 Merge합니다.
    """
    
    def __init__(self, llm_async_callable: Callable[[str, str, Dict], Awaitable[str]]):
        """
        :param llm_async_callable: 실제 LLM API를 호출할 비동기 함수. 
               서명: async def call_llm(system_prompt: str, user_prompt: str, schema: dict) -> str
        """
        self.llm_async_callable = llm_async_callable

    async def _run_agent(self, agent: ASMRAgent, context_data: str) -> Dict[str, Any]:
        """개별 에이전트에 데이터를 먹이고 결과를 받아오는 래퍼 함수"""
        try:
            # LLM 호출
            response_text = await self.llm_async_callable(
                agent.system_prompt,
                context_data,
                agent.json_schema
            )
            
            # JSON 파싱 시도 (LLM이 JSON 텍스트를 반환한다고 가정)
            try:
                result_data = json.loads(response_text)
            except json.JSONDecodeError:
                result_data = {"raw_text": response_text}

            return {
                "agent_name": agent.name,
                "status": "success",
                "data": result_data
            }
        except Exception as e:
            logger.error(f"Agent {agent.name} failed: {str(e)}")
            return {
                "agent_name": agent.name,
                "status": "error",
                "error": str(e)
            }

    async def run_parallel_analysis(self, agents: List[ASMRAgent], context_data: str) -> Dict[str, Any]:
        """
        주어진 세션/문서 데이터를 여러 에이전트가 동시에 읽고 팩트를 추출합니다.
        :param agents: 분석을 수행할 ASMR 에이전트 목록 (예: FactAgent, TimelineAgent 등)
        :param context_data: 대상 텍스트 (로그, 의료기록 등)
        :return: 병합된 분석 결과 딕셔너리
        """
        tasks = [self._run_agent(agent, context_data) for agent in agents]
        
        # asyncio.gather를 사용해 완전 병렬로 LLM Request 실행
        results = await asyncio.gather(*tasks)
        
        merged_report = {
            "orchestration_status": "completed",
            "agent_results": {}
        }
        
        for res in results:
            merged_report["agent_results"][res["agent_name"]] = res
            
        return merged_report

# 사용 예시 (더미용)
# if __name__ == "__main__":
#     async def mock_llm_call(sys_prompt, user_prompt, schema):
#         await asyncio.sleep(1) # 네트워크 딜레이 시뮬레이션
#         return '{"summary": "mocked result"}'
#     
#     orchestrator = ASMRParallelOrchestrator(llm_async_callable=mock_llm_call)
#     agents = [
#         ASMRAgent("FactSearcher", "너는 팩트만 추출한다."),
#         ASMRAgent("TimelineTracker", "너는 시간대별로 정보를 나열한다.")
#     ]
#     
#     async def test():
#         result = await orchestrator.run_parallel_analysis(agents, "여기에 긴 히스토리 텍스트")
#         print(json.dumps(result, indent=2, ensure_ascii=False))
#         
#     asyncio.run(test())
