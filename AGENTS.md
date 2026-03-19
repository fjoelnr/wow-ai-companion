# AGENTS.md

## Purpose

This repository contains the WoW AI Companion addon plus supporting Python/MCP services.
This file is the repo memory for AI coding agents.

## Repository Map

- `addon/` WoW addon source (Lua + TOC)
- `agents/` Python agent components (`coach`, `planner`, `retriever`, `validator`)
- `mcp-server/` MCP tool server and ingestion/lookup tools
- `external/python/` runtime integration scripts and prompts
- `docs/` setup, architecture, troubleshooting, and workflow docs
- `tools/` local utility scripts (for example WoW copy helper)

## Context Hierarchy

1. `AGENTS.md` (global context)
2. `.agents/context-index.md` (repository navigation)
3. nearest directory-level `AGENT.md` (local context)
4. `.agents/workflows/` (procedures)
5. `.agents/skills/` (reasoning patterns)
6. `.agents/guardrails/` (constraints)

## Working Rules

- Prefer small, reviewable changes with clear impact.
- Keep addon Lua logic and Python/MCP logic separated.
- Update documentation when behavior or setup changes.
- Respect guardrails for release and ingestion paths.
- Keep detailed gotchas in local `AGENT.md` files near risky modules.
