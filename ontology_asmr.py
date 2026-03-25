from typing import List, Dict, Any
from .core import ASMRAgent, ASMRParallelOrchestrator

def get_ontology_traversal_agents() -> list[ASMRAgent]:
    """
    [Phase 3] 온톨로지(지식 그래프)를 순회(Traversal)하며 정보를 탐색하는 에이전트.
    초거대 그래프를 다 넘기기엔 토큰 낭비가 심하므로, 특정 Sub-Graph(노드+엣지 모음)를 
    텍스트화하여 컨텍스트로 주입받고, 이를 해석합니다.
    """
    
    # 1. 엣지 해석기(Edge Interpreter)
    edge_agent = ASMRAgent(
        name="EdgeInterpreterAgent",
        system_prompt=(
            "너는 지식그래프(Ontology)의 엣지(관계)를 전담하여 해석하는 에이전트야. "
            "현재 노드와 주변 노드들이 어떤 관계(Is-A, Has-A, Treated-By 등)로 엮여 있는지 분석하고, "
            "이 관계망이 사용자의 질문(또는 진단)에 어떤 핵심 힌트를 주는지 도출해."
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
                            "insight": {"type": "string", "description": "해당 관계가 주는 의미"}
                        }
                    }
                }
            }
        }
    )
    
    # 2. 경로 탐색 제안자(Pathfinder)
    pathfinder_agent = ASMRAgent(
        name="PathfinderAgent",
        system_prompt=(
            "너는 지식그래프 망에서 다음에 어디로 이동해야 할지(Hop) 경로를 제안하는 에이전트야. "
            "현재까지 주어진 정보가 불충분할 경우, 추가 질문이나 연관 노드로의 확장을 제안해."
        ),
        json_schema={
            "type": "object",
            "properties": {
                "suggested_next_hops": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "description": "다음에 조회해야 할 노드의 이름이나 카테고리"
                    }
                },
                "reason": {
                    "type": "string",
                    "description": "왜 그 노드로 탐색을 확장해야 하는가?"
                }
            }
        }
    )
    
    return [edge_agent, pathfinder_agent]

class OntologyASMRSearcher:
    """
    Dr.Claw 시스템 내의 온톨로지 지식망이나 NDB(Namyangju Baek Hospital) 지식망에
    ASMR 병렬 추론을 붙이는 래퍼 로직입니다.
    """
    def __init__(self, orchestrator: ASMRParallelOrchestrator):
        self.orchestrator = orchestrator
        self.agents = get_ontology_traversal_agents()
        
    async def traverse_subgraph(self, subgraph_json: str):
        """특정 서브그래프 데이터(JSON 또는 Markdown 포맷)를 읽고 추론합니다."""
        results = await self.orchestrator.run_parallel_analysis(self.agents, subgraph_json)
        return results
