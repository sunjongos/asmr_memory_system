---
name: "ASMR Memory System (Core)"
description: "Supermemory.ai의 ASMR(Agentic Search and Memory Retrieval) 기법을 모듈화한 통합 스킬. 한 번의 요청을 여러 개의 병렬 에이전트 전담 요원(Fact, Context, Timeline 등)으로 나누어 비동기 인지 및 병합 엔진을 제공합니다."
---

# ASMR Memory System Skill

이 폴더는 다중 에이전트 인지 시스템을 전담하는 **통합 공통 모듈**입니다.
`luca_manager`, `ontology_ndb`, `ontology-dreye_AIagent` 등 다른 메인 파이프라인에서 이 모듈을 import하여 사용합니다.

## 디렉토리 구조
- `core.py`: 비동기 동시 프롬프팅 및 오케스트레이션을 담당하는 핵심 엔진
- `luca_observer.py`: Luca의 장기 기억망을 백그라운드로 정리하는 Observer Agents (개발 예정)
- `dr_claw_search.py`: Dr.Claw 등 의료 데이터를 삼면(Fact, Context, Causal)으로 읽어내는 Search Agents (개발 예정)

## 핵심 설계 철학
- **No Vector Search Reliance**: 수학적 거리에 기반한 검색을 벗어나 철저한 "Agentic Reasoning(에이전트 인지)"을 사용
- **Parallel Dispatch**: LLM I/O 병목을 해결하기 위해, 각 역할 에이전트 파이프라인은 파이썬 `asyncio`로 완전 병렬 실행
