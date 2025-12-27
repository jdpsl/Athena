"""Stdio transport for MCP client."""

import asyncio
import json
import os
from typing import Optional

from .client import MCPClient


class StdioMCPClient(MCPClient):
    """MCP client using stdio transport (subprocess)."""

    def __init__(
        self,
        server_name: str,
        command: str,
        args: Optional[list[str]] = None,
        env: Optional[dict[str, str]] = None,
        timeout: int = 30
    ):
        super().__init__(server_name, timeout)
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.process: Optional[asyncio.subprocess.Process] = None

    async def connect(self) -> None:
        """Launch subprocess and establish connection."""
        env = os.environ.copy()
        env.update(self.env)

        self.process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )

    async def disconnect(self) -> None:
        """Terminate subprocess."""
        if self.process:
            self.process.terminate()
            await self.process.wait()

    async def send_request(self, method: str, params: Optional[dict] = None) -> dict:
        """Send JSON-RPC request via stdin/stdout."""
        if not self.process:
            raise RuntimeError("Client not connected")

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }

        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()

        # Read response (with timeout)
        try:
            response_line = await asyncio.wait_for(
                self.process.stdout.readline(),
                timeout=self.timeout
            )
            return json.loads(response_line.decode())
        except asyncio.TimeoutError:
            raise TimeoutError(f"MCP server '{self.server_name}' timed out")
