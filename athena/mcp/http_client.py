"""HTTP transport for MCP client."""

import httpx
from typing import Optional

from .client import MCPClient


class HttpMCPClient(MCPClient):
    """MCP client using HTTP transport."""

    def __init__(self, server_name: str, url: str, timeout: int = 30):
        super().__init__(server_name, timeout)
        self.url = url
        self.http_client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> None:
        """Create HTTP client."""
        self.http_client = httpx.AsyncClient(timeout=self.timeout)

    async def disconnect(self) -> None:
        """Close HTTP client."""
        if self.http_client:
            await self.http_client.aclose()

    async def send_request(self, method: str, params: Optional[dict] = None) -> dict:
        """Send JSON-RPC request via HTTP POST."""
        if not self.http_client:
            raise RuntimeError("Client not connected")

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }

        response = await self.http_client.post(self.url, json=request)
        response.raise_for_status()
        return response.json()
