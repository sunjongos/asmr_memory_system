import asyncio
import json
import argparse
import sys
import logging

from .core import ASMRParallelOrchestrator
from .dr_claw_search import DrClawSearchOrchestrator
from .luca_observer import LucaMemoryObserver

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# 더미 LLM 호출기 (실제 프로덕션에서는 OpenAI, Anthropic, Gemini API 통신 코드를 여기에 붙입니다)
async def dummy_llm_call(system_prompt: str, user_prompt: str, json_schema: dict) -> str:
    """Claude Code나 실제 환경 파이프라인에서 돌아갈 때 LLM을 호출하는 로직입니다."""
    # 현재는 CLI 시연을 위해 더미 JSON을 반환합니다.
    dummy_result = {
        "status": "mocked",
        "fact_or_context": f"Simulated insights for prompt length {len(user_prompt)}"
    }
    await asyncio.sleep(0.5)
    return json.dumps(dummy_result)

async def run_query(question: str):
    print(f"🧠 [ASMR CLI] 질의를 5050 Port 공유 메모리로 전송합니다: '{question}'")
    core_engine = ASMRParallelOrchestrator(llm_async_callable=dummy_llm_call)
    dr_claw = DrClawSearchOrchestrator(orchestrator=core_engine)
    
    result = await dr_claw.analyze_from_5050_memory(question)
    
    print("\n✅ [ASMR 분석 결과 (JSON)]")
    print(json.dumps(result, indent=2, ensure_ascii=False))

async def run_observe(log_text: str):
    print(f"🕵️ [ASMR CLI] 백그라운드 Observer가 세션 로그를 분석하고 5050 포트에 저장합니다...")
    core_engine = ASMRParallelOrchestrator(llm_async_callable=dummy_llm_call)
    observer = LucaMemoryObserver(orchestrator=core_engine)
    
    result = await observer.process_session_log(log_text)
    
    print("\n✅ [Observer 정리 결과 (JSON)]")
    print(json.dumps(result, indent=2, ensure_ascii=False))

def main():
    parser = argparse.ArgumentParser(description="ASMR Memory System - Claude Code 전용 CLI 래퍼")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 1. 쿼리 (검색)
    p_query = subparsers.add_parser("query", help="Port 5050 메모리를 바탕으로 3인방 에이전트 다면 분석 실행")
    p_query.add_argument("question", type=str, help="검색할 질문 (의료 로그나 일반 질문)")
    
    # 2. 관찰 및 업데이트 (저장)
    p_observe = subparsers.add_parser("observe", help="대화/로그 텍스트를 읽고 ASMR 모델로 분해하여 Port 5050에 저장")
    p_observe.add_argument("log", type=str, help="분석/저장할 텍스트 파일 내용 또는 기록")

    args = parser.parse_args()
    
    if args.command == "query":
        asyncio.run(run_query(args.question))
    elif args.command == "observe":
        asyncio.run(run_observe(args.log))

if __name__ == "__main__":
    main()
