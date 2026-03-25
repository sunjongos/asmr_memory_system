import json
import httpx
import logging

logger = logging.getLogger(__name__)

API_URL = "http://localhost:5050"
DEFAULT_AGENT_ID = "Luca_ASMR"


class Port5050Error(Exception):
    """Port 5050 communication failure."""
    pass


class Port5050Bridge:
    """
    Port 5050 shared long-term memory server bridge with connection pooling.
    Reuses a single httpx.AsyncClient across all requests to avoid
    repeated TCP handshake overhead.
    """

    def __init__(self, api_url: str = API_URL):
        self.api_url = api_url
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                timeout=httpx.Timeout(60.0, connect=5.0),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def health_check(self) -> bool:
        """Verify that Port 5050 server is reachable before running analysis."""
        client = await self._get_client()

        # Try /health first (fast path)
        try:
            resp = await client.get("/health", timeout=5.0)
            if resp.status_code == 200:
                return True
        except Exception:
            pass

        # Fallback: /query with minimal payload (5050 may lack /health endpoint)
        try:
            resp = await client.post(
                "/query",
                json={"question": "ping", "agent_id": "healthcheck"},
                timeout=20.0,
            )
            return resp.status_code == 200
        except Exception:
            return False

    async def fetch_raw_memory(self, question: str, agent_id: str = DEFAULT_AGENT_ID) -> str:
        """
        Fetch initial long-term memory context from Port 5050 /query.
        Raises Port5050Error on failure instead of silently returning empty string.
        """
        client = await self._get_client()
        try:
            response = await client.post(
                "/query",
                json={"question": question, "agent_id": agent_id},
            )
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", "")
                if not result or not result.strip():
                    raise Port5050Error(
                        f"Port 5050 returned empty result for question: '{question[:80]}...'"
                    )
                return result
            else:
                raise Port5050Error(
                    f"Port 5050 HTTP {response.status_code}: {response.text[:200]}"
                )
        except Port5050Error:
            raise
        except httpx.ConnectError:
            raise Port5050Error(
                "Cannot connect to Port 5050. Is the memory server running? "
                "(python shared_memory_server.py or equivalent)"
            )
        except httpx.TimeoutException:
            raise Port5050Error("Port 5050 request timed out (>10s)")
        except Exception as e:
            raise Port5050Error(f"Unexpected error communicating with Port 5050: {e}")

    async def ingest_memory(
        self,
        content: str,
        title: str = "ASMR Insight",
        agent_id: str = DEFAULT_AGENT_ID,
    ) -> bool:
        """
        Ingest high-purity ASMR analysis results back into long-term memory.
        Returns True on success, raises Port5050Error on failure.
        """
        text = f"[{title}]\n{content}"
        client = await self._get_client()
        try:
            response = await client.post(
                "/ingest",
                json={"text": text, "agent_id": agent_id},
            )
            if response.status_code == 200:
                logger.info(f"Ingested to 5050: '{title}' ({len(content)} chars)")
                return True
            else:
                raise Port5050Error(
                    f"Ingest failed HTTP {response.status_code}: {response.text[:200]}"
                )
        except Port5050Error:
            raise
        except httpx.ConnectError:
            raise Port5050Error("Cannot connect to Port 5050 for ingest")
        except httpx.TimeoutException:
            raise Port5050Error("Port 5050 ingest timed out")
        except Exception as e:
            raise Port5050Error(f"Unexpected ingest error: {e}")
