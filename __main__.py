import asyncio
import json
import argparse
import sys
import logging
import httpx
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .core import ASMRParallelOrchestrator
from .dr_claw_search import DrClawSearchOrchestrator
from .luca_observer import LucaMemoryObserver

async def gemini_llm_call(system_prompt: str, user_prompt: str, json_schema: dict) -> str:
    """GEMINI_API_KEY 환경변수를 사용하여 실제 Gemini 2.5 Flash API를 호출합니다."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return json.dumps({"error": "GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다."})
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # 시스템 프롬프트에 엄격한 JSON 반환 지시 추가
    schema_str = json.dumps(json_schema, ensure_ascii=False) if json_schema else "{}"
    full_system_prompt = system_prompt + f"\n\n[중요 지시사항]\n반드시 아래 JSON 스키마 규격에 맞춰 순수한 JSON 문자열만 반환해야 합니다. 마크다운 기호(```json 등)는 포함하지 마세요.\n스키마: {schema_str}"
    
    payload = {
        "systemInstruction": {"parts": [{"text": full_system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"temperature": 0.2}
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, timeout=30.0)
        if resp.status_code != 200:
            return json.dumps({"error": f"Gemini API Error: {resp.text}"})
            
        data = resp.json()
        try:
            text_response = data['candidates'][0]['content']['parts'][0]['text']
            
            # 마크다운 방어 로직 (```json ... ``` 제거)
            text_response = text_response.strip()
            if text_response.startswith('```json'): text_response = text_response[7:]
            if text_response.startswith('```'): text_response = text_response[3:]
            if text_response.endswith('```'): text_response = text_response[:-3]
                
            return text_response.strip()
        except KeyError:
            return json.dumps({"error": "Failed to parse API response"})

async def run_query(question: str):
    print(f"🧠 [ASMR CLI] 질의를 5050 Port 공유 메모리로 전송합니다: '{question}'")
    core_engine = ASMRParallelOrchestrator(llm_async_callable=gemini_llm_call)
    dr_claw = DrClawSearchOrchestrator(orchestrator=core_engine)
    
    result = await dr_claw.analyze_from_5050_memory(question)
    
    print("\n✅ [ASMR 분석 결과 (JSON)]")
    print(json.dumps(result, indent=2, ensure_ascii=False))

async def run_observe(log_text: str):
    print(f"🕵️ [ASMR CLI] 백그라운드 Observer가 세션 로그를 분석하고 5050 포트에 저장합니다...")
    core_engine = ASMRParallelOrchestrator(llm_async_callable=gemini_llm_call)
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
