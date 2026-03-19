# Status

## Product Status

`wow-ai-companion` is an active prototype-stage project.

The core idea is already visible:

- the addon can collect and display guidance
- the external runtime can ingest exported context
- an MCP/LLM pipeline can generate recommendations

The project is not yet polished as a user-facing package and still needs setup hardening, clearer onboarding, and broader validation.

## What Works

- addon structure and command flow
- Docker-based local stack
- external watcher/runtime base
- MCP-based analysis pattern
- ANR repository scaffolding

## What Still Needs Work

- stronger end-user README and setup flow
- better validation of common WoW installation paths
- clearer separation of stable vs experimental features
- more implementation-level tests
- more polished examples and screenshots

## Safety Boundary

This repository is guidance-only by design.

- no gameplay automation
- no hidden input execution
- no addon-side network logic

## Next Improvement Areas

- setup documentation quality
- architecture consistency across addon, agents, and MCP server
- stronger examples for common use cases
- release hardening for public consumption
