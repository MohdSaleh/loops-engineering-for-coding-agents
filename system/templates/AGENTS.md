# Agentic Project Execution Entry Point

This repository contains a user project governed by Loop Engineering v3.0.

## Mandatory boot order

1. Read `.agentic/config/workspace.json`.
2. Read `.agentic/protocol/LOOP-ENGINEERING-v3.0.md` completely.
3. Read `.agentic/policy/PROJECT-SPEC.md`, `.agentic/policy/REQUIREMENTS.json`, and `.agentic/policy/VISION.md`.
4. Rebuild and validate runtime projections before changing project files.
5. Treat every ordinary user coding prompt as a `PROJECT_TASK` for the declared project unless the user explicitly requests project creation, project-wide planning, or control-plane maintenance.

## Hard boundary

- The user application remains in its normal framework-native paths.
- `.agentic/**` and this `AGENTS.md` are system/control-plane paths.
- A maker working on a project goal MUST NOT edit control-plane paths.
- A `SYSTEM_MAINTENANCE` goal requires explicit user authorization and a separate goal record.
- Candidate changes are accepted only when every changed path is allowed by the active goal and `workspace.json`.

The full rules are authoritative in `.agentic/protocol/LOOP-ENGINEERING-v3.0.md`.
