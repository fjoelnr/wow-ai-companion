# Guardrail: Architecture Rules

1. Keep WoW addon Lua logic isolated under `addon/`.
2. Keep Python agent orchestration isolated under `agents/` and `external/python/`.
3. Keep MCP server contracts and tool logic isolated under `mcp-server/`.
4. Cross-layer changes must update relevant docs in `docs/`.
