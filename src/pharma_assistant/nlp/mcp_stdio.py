"""Small MCP stdio adapter for the agent's read-only tools (JSON-RPC 2.0)."""

import json
from typing import TextIO

from pharma_assistant.nlp.agent import PharmacyTools


def serve(tools: PharmacyTools, input_stream: TextIO, output_stream: TextIO) -> None:
    """Serve initialization, ping and tool discovery/calls; stdout is protocol only."""
    initialized = False
    for line in input_stream:
        identifier = None
        try:
            if len(line) > 65536:
                raise ValueError("Oversized protocol message")
            request = json.loads(line)
            if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
                raise ValueError("Invalid JSON-RPC request")
            identifier = request.get("id")
            method = request.get("method")
            params = request.get("params", {})
            if not isinstance(params, dict):
                raise ValueError("Invalid parameters")
            if identifier is None:
                continue
            if method == "initialize":
                requested = params.get("protocolVersion")
                version = (
                    requested
                    if requested in {"2024-11-05", "2025-03-26", "2025-06-18"}
                    else "2025-06-18"
                )
                result = {
                    "protocolVersion": version,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "pharma-ai-tools", "version": "0.2.0"},
                }
                initialized = True
            elif method == "ping":
                result = {}
            elif not initialized:
                raise ValueError("Initialize first")
            elif method == "tools/list":
                result = {"tools": tools.definitions()}
            elif method == "tools/call":
                name = params.get("name")
                if name not in {d["name"] for d in tools.definitions()}:
                    raise ValueError("Unknown tool")
                try:
                    # Every MCP invocation has an independent bounded read-only budget.
                    registry = PharmacyTools(tools.baseline, tools.provider)
                    value = registry.call(name, params.get("arguments", {}))
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(value, ensure_ascii=False),
                            }
                        ],
                        "structuredContent": value,
                        "isError": False,
                    }
                except (ValueError, OSError):
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": "Tool unavailable or invalid arguments",
                            }
                        ],
                        "isError": True,
                    }
            else:
                output_stream.write(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "id": identifier,
                            "error": {"code": -32601, "message": "Method not found"},
                        }
                    )
                    + "\n"
                )
                output_stream.flush()
                continue
            response = {"jsonrpc": "2.0", "id": identifier, "result": result}
        except (ValueError, TypeError):
            response = {
                "jsonrpc": "2.0",
                "id": identifier,
                "error": {"code": -32602, "message": "Invalid request or parameters"},
            }
        output_stream.write(json.dumps(response, ensure_ascii=False) + "\n")
        output_stream.flush()
