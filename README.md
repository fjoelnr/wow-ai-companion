# WoW AI Companion

A ToS-compliant World of Warcraft AI copilot for guidance, review, and second-screen recommendations.

This project is intentionally **not** a bot and **not** an automation layer. It collects player context, runs external analysis, and returns tips to the player without sending input back into the game client.

## What It Does

- WoW addon for snapshot export and in-game tip display
- external Python watcher for SavedVariables and combat log ingestion
- MCP server for tool-style analysis and tip generation
- local-first LLM runtime via Ollama, with optional API fallback

## What It Does Not Do

- no input automation
- no rotation botting
- no movement, combat, or interaction execution
- no hidden network logic inside the addon

## Current Focus

Version focus is currently on:

- exploration and quest support
- collecting, rares, and route hints
- data export and second-screen analysis

Combat coaching is a later stage and remains guidance-only.

## Repository Layout

```text
addon/            WoW addon source (Lua)
agents/           planner / retriever / validator / coach logic
mcp-server/       MCP and analysis server
external/python/  watcher runtime and prompts
docs/             setup, architecture, privacy, troubleshooting
tools/            local helper scripts
.agents/          ANR context, workflows, skills, guardrails
```

## Quick Start

1. Clone the repository.
2. Copy `addon/AICompanion` into your WoW AddOns directory.
3. Start the external stack with Docker.
4. Export a game snapshot in WoW.
5. Review generated recommendations in game.

English quickstart:
- [docs/QUICKSTART.md](docs/QUICKSTART.md)

German quickstart:
- [docs/QUICKSTART_DE.md](docs/QUICKSTART_DE.md)

Supporting setup docs:
- [docs/SETUP_WINDOWS_WOW.md](docs/SETUP_WINDOWS_WOW.md)
- [docs/SETUP_SERVER_DOCKER.md](docs/SETUP_SERVER_DOCKER.md)
- [docs/ENV_VARS.md](docs/ENV_VARS.md)
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## Architecture

High-level flow:

1. The addon exports structured state from the game client.
2. The watcher observes SavedVariables and combat logs outside the client.
3. The MCP server enriches and validates the data.
4. The LLM layer generates recommendations.
5. The addon renders tips back to the player.

Further reading:
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/PRIVACY.md](docs/PRIVACY.md)
- [docs/STATUS.md](docs/STATUS.md)

## Safety and ToS Position

This repository is designed around a strict constraint:

- the addon observes and displays
- the external stack analyzes
- the player decides and acts

No gameplay automation is part of the intended product scope.

## ANR Context Layer

This repository also serves as a practical ANR-style example for agent-readable project structure.

- global context: [AGENTS.md](AGENTS.md)
- repository index: [.agents/context-index.md](.agents/context-index.md)
- local context: `AGENT.md` files near high-risk areas
- reusable workflows, skills, and guardrails in `.agents/`

The goal is not documentation volume. The goal is making the repository understandable to both humans and coding agents.

## Status

The project is in active early-stage development.

- addon, watcher, and MCP structure exist
- Docker workflow exists
- documentation baseline exists
- product polish, setup hardening, and clearer user-facing onboarding are still in progress

See [docs/STATUS.md](docs/STATUS.md) and [docs/ROADMAP.md](docs/ROADMAP.md).

## Branching

- `develop` is the default integration branch
- feature work goes to `feature/*` branches and merges into `develop`
- `main` is the release branch and is promoted from `develop`

See [docs/WORKFLOW_GIT.md](docs/WORKFLOW_GIT.md).

## Licensing

This repository uses split licensing by component:

- addon and repository-level project material: MIT, see [LICENSE](LICENSE)
- external runtime and MCP-oriented service code: Apache-2.0, see [LICENSE-APACHE](LICENSE-APACHE)

When contributing, keep that separation explicit.
