# 🧠 ASMR Memory System

**Agentic Search and Memory Retrieval (ASMR)** 엔진을 통합한 지능형 메모리 파이프라인.  
Supermemory.ai에서 제안된 '멀티-에이전트 기반 독립 팩트 추출(Agentic Reasoning) 시스템'을 영구적인 공유 메모리 서버(Port 5050) 및 지식그래프(Ontology)와 결합한 세계관 스킬 플러그인입니다.

## 🚀 기획 의도 및 특징

기존의 **RAG(Retrieval-Augmented Generation)**은 단순히 질문과 유사한 백터(수학적 유사도) 문장 덩어리를 가져오기 때문에 '시간적 인과관계'나 '은유적 컨텍스트'를 엉뚱하게 조합하는 할루시네이션(기억상실증) 문제를 안고 있습니다.

이 리포지토리는 RAG를 완벽하게 대체하는 **ASMR 파이프라인**을 제공합니다.
1. **Parallel Observer Agents**: 질문이나 대화가 발생할 때, [ 팩트 전담 / 컨텍스트 전담 / 타임라인-인과 전담 ] 3~4명의 AI 요원이 동시에 `asyncio` 기반으로 원시 데이터를 입체적으로 분해합니다.
2. **Port 5050 Shared Memory Bridge**: RAG의 심각한 한계를 극복하기 위해, 물리적 저장소인 5050 포트 서버에서 1차로 가져온 대량의 원시 지식이나 대화 기록을 이 요원들이 다시 재구성합니다.
3. **Ontology Traversal**: 평면적인 텍스트뿐만 아니라 Knowledge Graph(온톨로지) 구조의 노드를 탐색하는 Edge-Navigable 에이전트도 포함되어 있습니다.

## 📁 디렉토리 구조 및 핵심 모듈

- **`core.py`**  
  다중 LLM 요원들을 동시에 출격시키고, 결과를 종합(Orchestration)하는 코어 엔진입니다. (`asyncio.gather`를 통해 속도 병목 최소화)
  
- **`port_5050_bridge.py`**  
  기존의 중앙 공유 서버(`127.0.0.1:5050`)와 통신하여, ASMR 요원들이 퍼올릴 원시 데이터(`query`)를 가져오고, 최종 분석된 고순도의 통찰력을 다시 `ingest`하여 영구 기억으로 갱신하는 비동기 브릿지입니다.
  
- **`dr_claw_search.py`** *(의료/진단 특화 Search)*  
  환자의 임상 기록 데이터를 분석할 때, 의무기록 기반 팩트, 환자의 생활 컨텍스트, 증상의 시계열 변화를 3명의 요원이 각각 병렬 추론하여 진단 AI(Dr.Claw)에게 전달하는 어댑터입니다.

- **`luca_observer.py`** *(백그라운드 세션 관찰자)*  
  대화를 엿들으며 사용자의 선호도, 정책 변경(기존 사실의 폐기 및 업데이트), 타임라인을 추출하여 5050 포트에 조용히 병합시키는 백그라운드 스킬(Luca)입니다.

- **`ontology_asmr.py`** *(지식그래프 융합)*  
  온톨로지 형태의 JSON-LD나 마크다운 그래프를 순회하며 노드 폭발 없이 최적의 경로(Pathfinding)와 엣지(Edge/Relationship)의 숨은 의미를 해석하는 에이전트.

## 💻 사용 방법

이 모듈은 다른 Python 스킬이나 메인 AI 에이전트 파이프라인에서 수입(`import`)해 활용하는 코어 라이브러리 역할을 합니다.

```python
import asyncio
from asmr_memory_system.dr_claw_search import DrClawSearchOrchestrator
from asmr_memory_system.core import ASMRParallelOrchestrator

async def main():
    core_engine = ASMRParallelOrchestrator(llm_async_callable=my_llm_function)
    dr_claw = DrClawSearchOrchestrator(orchestrator=core_engine)
    
    # 5050 포트 메모리에서 자동으로 컨텍스트를 찾아 ASMR로 입체 분석!
    analysis = await dr_claw.analyze_from_5050_memory("최근 3일간 환자의 혈당 변화와 식단의 관계는?")
    print(analysis)

asyncio.run(main())
```

## 🤝 기여 (Contributing)
ASMR 논리와 온톨로지 융합 메커니즘을 함께 발전시킬 Contributor를 환영합니다! Pull Request나 Issue를 자유롭게 남겨주세요.
