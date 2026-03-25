import httpx
import logging

logger = logging.getLogger(__name__)

API_URL = "http://localhost:5050"
DEFAULT_AGENT_ID = "Luca_ASMR"

class Port5050Bridge:
    """
    기존의 RAG 기반 단순 검색을 수행하던 Port 5050 공유 장기 메모리 서버와 통신하는 비동기 브릿지입니다.
    이 브릿지를 통해 ASMR 오케스트레이터가 대규모 지식망(Graph DB)나 Vector DB에서 원시 컨텍스트를 퍼올립니다.
    """
    def __init__(self, api_url: str = API_URL):
        self.api_url = api_url
        
    async def fetch_raw_memory(self, question: str, agent_id: str = DEFAULT_AGENT_ID) -> str:
        """
        Port 5050 /query 엔드포인트를 호출하여 질문과 관련된 초기 장기 기억 덩어리를 가져옵니다.
        (기존 RAG 방식의 1차 검색)
        가져온 텍스트는 이후 ASMR 에이전트들의 병렬 분석(Fact/Context/Timeline)의 Context Data가 됩니다.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/query",
                    json={"question": question, "agent_id": agent_id},
                    timeout=10.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("result", "")
                else:
                    logger.error(f"Failed to fetch memory from 5050: {response.text}")
                    return f"Error fetching from 5050: {response.text}"
            except Exception as e:
                logger.error(f"Connection error to Port 5050: {e}")
                return ""

    async def ingest_memory(self, content: str, title: str = "ASMR Insight", agent_id: str = DEFAULT_AGENT_ID) -> bool:
        """
        Port 5050 /ingest 엔드포인트를 호출하여, ASMR 요원들이 병렬로 정리해낸 고순도의 결론을
        다시 장기 메모리에 정식으로 영구 저장합니다.
        """
        text = f"주제: {title}\n내용: {content}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/ingest",
                    json={"text": text, "agent_id": agent_id},
                    timeout=10.0
                )
                if response.status_code == 200:
                    return True
                else:
                    logger.error(f"Failed to ingest memory to 5050: {response.text}")
                    return False
            except Exception as e:
                logger.error(f"Connection error to Port 5050: {e}")
                return False
